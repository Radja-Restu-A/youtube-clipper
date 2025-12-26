from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import uuid
from typing import List
from datetime import datetime

# Import configuration
from config import (
    init_directories, DEVICE, MODEL_NAME, MAX_DURATION_SECONDS,
    CLIP_DURATION, TOP_CLIPS_COUNT, AUDIO_DIR, CLIPS_DIR, 
    SUBTITLES_DIR, OUTPUT_DIR, HISTORY_DIR, logger
)

# Import models
from models.schemas import YouTubeRequest

# Import repositories
from repositories.progress_repository import ProgressRepository
from repositories.history_repository import HistoryRepository

# Import services
from services.youtube_service import YouTubeService
from services.audio_service import AudioAnalysisService
from services.transcription_service import TranscriptionService
from services.clip_service import ClipDetectionService
from services.subtitle_service import SubtitleService
from services.video_service import VideoProcessingService

# Import utils
from utils.time_utils import parse_range_percent
from utils.file_utils import cleanup_temp_files

# Initialize FastAPI app
app = FastAPI(title="Whisper Subtitle API with Auto Clip")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize directories
init_directories()

# Initialize repositories
progress_repo = ProgressRepository()
history_repo = HistoryRepository(HISTORY_DIR)

# Initialize services
transcription_service = TranscriptionService(MODEL_NAME, DEVICE)
youtube_service = YouTubeService()
audio_service = AudioAnalysisService()
clip_service = ClipDetectionService()
subtitle_service = SubtitleService()
video_service = VideoProcessingService()


class VideoProcessor:
    """Main video processing orchestrator"""
    
    def __init__(self):
        self.youtube = youtube_service
        self.audio = audio_service
        self.transcription = transcription_service
        self.clip = clip_service
        self.subtitle = subtitle_service
        self.video = video_service
        self.progress = progress_repo
        self.history = history_repo
    
    def process(self, video_id: str, youtube_url: str, clip_duration: int, range_percent: str):
        """Main processing pipeline"""
        try:
            # Step 1: Validate video
            self.progress.update(video_id, "validating", 5, "Validating YouTube video...")
            video_info = self.youtube.get_video_info(youtube_url)
            total_duration = video_info['duration']
            
            if total_duration > MAX_DURATION_SECONDS:
                raise Exception(f"Video too long: {total_duration}s (max: {MAX_DURATION_SECONDS}s)")
            
            logger.info(f"Video: {video_info['title']} - {total_duration}s")
            
            # Step 2: Parse range
            range_start, range_end = parse_range_percent(range_percent, total_duration)
            actual_duration = range_end - range_start
            logger.info(f"Processing range: {range_percent}% ({range_start:.1f}s - {range_end:.1f}s)")
            
            # Step 3: Download audio
            self.progress.update(video_id, "downloading_audio", 10, 
                               f"Downloading audio (range: {range_percent}%)...")
            audio_path = self.youtube.download_audio_range(
                youtube_url, AUDIO_DIR, video_id, range_start, range_end
            )
            
            # Step 4: Transcribe
            self.progress.update(video_id, "transcribing", 20, 
                               "Transcribing audio with Whisper AI...")
            result = self.transcription.transcribe(audio_path)
            
            # Step 5: Analyze audio
            self.progress.update(video_id, "analyzing", 40, 
                               "Analyzing audio for best clips...")
            engagement_windows = self.audio.analyze_engagement(audio_path)
            
            # Step 6: Find top clips
            self.progress.update(video_id, "selecting_clips", 50, 
                               f"Selecting top {TOP_CLIPS_COUNT} clips...")
            top_clips = self.clip.find_top_clips(engagement_windows, clip_duration, TOP_CLIPS_COUNT)
            
            # Step 7: Process each clip
            clips_output = self._process_clips(
                video_id, youtube_url, top_clips, clip_duration, 
                range_start, result
            )
            
            # Step 8: Finalize
            self.progress.update(video_id, "finalizing", 95, "Finalizing...")
            self._save_metadata(video_id, youtube_url, video_info, range_percent, 
                              range_start, range_end, actual_duration, clips_output)
            
            # Save history
            self.history.save(video_id, video_info, clips_output, range_percent)
            
            # Cleanup
            self._cleanup(video_id)
            
            # Complete
            self.progress.update(video_id, "completed", 100, 
                               f"Completed! {len(clips_output)} clips ready")
            self.progress.add_metadata(
                video_id,
                clips=clips_output,
                video_info=video_info,
                range_percent=range_percent,
                total_clips=len(clips_output)
            )
            
            logger.info(f"Processing completed for {video_id}")
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            self.progress.update(video_id, "error", 0, str(e))
    
    def _process_clips(self, video_id: str, youtube_url: str, top_clips: List[dict], 
                      clip_duration: int, range_start: float, transcription_result: dict) -> List[dict]:
        """Process each individual clip"""
        clips_output = []
        
        for idx, clip_info in enumerate(top_clips):
            progress = 50 + (idx * 8)
            self.progress.update(video_id, "processing_clip", progress, 
                               f"Processing clip {idx + 1}/{len(top_clips)}...")
            
            clip_id = f"{video_id}_clip_{idx + 1}"
            
            # Calculate absolute times
            clip_start_in_range = clip_info['start']
            clip_end_in_range = clip_info['end']
            absolute_clip_start = range_start + clip_start_in_range
            absolute_clip_end = range_start + clip_end_in_range
            
            # Download video clip
            raw_clip_path = CLIPS_DIR / f"{clip_id}_raw.mp4"
            
            if not self.youtube.download_video_clip(youtube_url, absolute_clip_start, 
                                                    clip_duration, raw_clip_path):
                if not self.youtube.extract_clip_with_ffmpeg(youtube_url, absolute_clip_start, 
                                                             clip_duration, raw_clip_path):
                    logger.warning(f"Failed to download clip {idx + 1}, skipping...")
                    continue
            
            # Extract words for this clip
            clip_words = self.subtitle.extract_clip_words(
                transcription_result, clip_start_in_range, clip_end_in_range
            )
            
            # Create subtitle
            ass_path = SUBTITLES_DIR / f"{clip_id}.ass"
            self.subtitle.create_ass_subtitle(clip_words, ass_path)
            
            # Burn subtitle
            output_path = OUTPUT_DIR / f"{clip_id}_subtitled.mp4"
            self.video.burn_subtitle(raw_clip_path, ass_path, output_path)
            
            # Save clip info
            clips_output.append({
                "clip_id": clip_id,
                "clip_number": idx + 1,
                "start_time": absolute_clip_start,
                "end_time": absolute_clip_end,
                "duration": clip_duration,
                "engagement_score": clip_info['engagement_score'],
                "output_file": str(output_path),
                "word_count": len(clip_words)
            })
        
        return clips_output
    
    def _save_metadata(self, video_id: str, youtube_url: str, video_info: dict, 
                      range_percent: str, range_start: float, range_end: float, 
                      actual_duration: float, clips: List[dict]):
        """Save processing metadata"""
        metadata = {
            "video_id": video_id,
            "youtube_url": youtube_url,
            "video_info": video_info,
            "range_percent": range_percent,
            "range_seconds": {
                "start": range_start,
                "end": range_end,
                "duration": actual_duration
            },
            "total_clips": len(clips),
            "clips": clips,
            "processed_at": datetime.now().isoformat()
        }
        
        metadata_path = OUTPUT_DIR / f"{video_id}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _cleanup(self, video_id: str):
        """Cleanup temporary files"""
        patterns = [
            AUDIO_DIR / f"{video_id}.*",
            CLIPS_DIR / f"{video_id}_clip_*_raw.*",
        ]
        cleanup_temp_files(video_id, patterns)


# Initialize processor
video_processor = VideoProcessor()


# ==============================================
# API ROUTES
# ==============================================

@app.get("/")
def read_root():
    """API information endpoint"""
    return {
        "message": "Whisper Subtitle API with YouTube Auto Clip",
        "device": DEVICE,
        "model": MODEL_NAME,
        "features": [
            "YouTube URL input (no full download)",
            "Audio-first processing",
            "Range selector (0-25, 26-50, 51-75, 76-100)",
            "Auto clip detection (engagement-based)",
            "Top 5 clips with burned subtitles",
            "Max duration: 2 hours"
        ],
        "endpoints": {
            "POST /process": "Process YouTube video",
            "GET /progress/{video_id}": "Get processing progress",
            "GET /download/{video_id}/{clip_number}": "Download specific clip",
            "GET /clips/{video_id}": "Get all clips info",
            "GET /history": "Get processing history"
        }
    }


@app.post("/process")
async def process_youtube(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """Process YouTube video endpoint"""
    try:
        # Validate URL
        if 'youtube.com' not in request.youtube_url and 'youtu.be' not in request.youtube_url:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Validate range format
        if request.range_percent:
            try:
                start_p, end_p = map(int, request.range_percent.split('-'))
                if not (0 <= start_p < end_p <= 100):
                    raise ValueError()
            except:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid range_percent. Use format: '0-25', '26-50', '51-75', or '76-100'"
                )
        
        # Generate video ID
        video_id = str(uuid.uuid4())
        
        # Initialize progress
        progress_repo.update(video_id, "queued", 0, "Video queued for processing")
        
        # Start processing in background
        background_tasks.add_task(
            video_processor.process,
            video_id,
            request.youtube_url,
            request.clip_duration or CLIP_DURATION,
            request.range_percent or "0-100"
        )
        
        return {
            "status": "processing",
            "video_id": video_id,
            "range_percent": request.range_percent or "0-100",
            "message": "Processing started. Use /progress/{video_id} to check status"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/progress/{video_id}")
async def get_progress(video_id: str):
    """Get processing progress"""
    if not progress_repo.exists(video_id):
        raise HTTPException(status_code=404, detail="Video ID not found")
    
    return progress_repo.get(video_id)


@app.get("/clips/{video_id}")
async def get_clips_info(video_id: str):
    """Get information about all clips for a video"""
    try:
        metadata_path = OUTPUT_DIR / f"{video_id}_metadata.json"
        
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Clips not found")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clips info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{video_id}/{clip_number}")
async def download_clip(video_id: str, clip_number: int):
    """Download specific clip"""
    try:
        clip_id = f"{video_id}_clip_{clip_number}"
        output_file = OUTPUT_DIR / f"{clip_id}_subtitled.mp4"
        
        if not output_file.exists():
            raise HTTPException(status_code=404, detail="Clip not found")
        
        return FileResponse(
            path=str(output_file),
            filename=f"clip_{clip_number}_subtitled.mp4",
            media_type="video/mp4"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading clip: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history():
    """Get processing history"""
    try:
        history = history_repo.get_all()
        return {"history": history}
    except Exception as e:
        logger.error(f"Error loading history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)