from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import json
import uuid
from typing import List
from datetime import datetime

# Import configuration
from config import (
    init_directories, DEVICE, MODEL_NAME, MAX_DURATION_SECONDS,
    CLIP_DURATION, TOP_CLIPS_COUNT, AUDIO_DIR, CLIPS_DIR, 
    SUBTITLES_DIR, OUTPUT_DIR, HISTORY_DIR, logger,
    CONTEXT_CLIP_MIN_DURATION, CONTEXT_CLIP_MAX_DURATION, CONTEXT_DURATION_FLEX,
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TIMEOUT, GEMINI_MAX_RETRIES,
    MIN_CLIPS_COUNT, MAX_CLIPS_COUNT
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
from services.context_analysis_service import ContextAnalysisService
from services.subtitle_service import SubtitleService
from services.video_service import VideoProcessingService
from services.gemini_viral_analyzer import GeminiViralAnalyzer
from services.history_service import OutputHistoryService

# Import utils
from utils.time_utils import parse_range_percent
from utils.file_utils import cleanup_temp_files

# Initialize FastAPI app
app = FastAPI(title="Whisper Subtitle API with Auto Clip")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

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
context_service = ContextAnalysisService()  # 🆕 NEW
subtitle_service = SubtitleService()
video_service = VideoProcessingService()
output_history_service = OutputHistoryService(OUTPUT_DIR)

# Initialize services gemini
gemini_analyzer = None
if GEMINI_API_KEY:
    try:
        gemini_analyzer = GeminiViralAnalyzer(GEMINI_API_KEY, GEMINI_MODEL)
        logger.info("✅ Gemini Viral Analyzer enabled")
    except Exception as e:
        logger.warning(f"⚠️ Gemini Viral Analyzer disabled: {e}")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set - viral mode unavailable")


class VideoProcessor:
    """Main video processing orchestrator"""
    
    def __init__(self):
        self.youtube = youtube_service
        self.audio = audio_service
        self.transcription = transcription_service
        self.clip = clip_service
        self.context = context_service
        self.gemini = gemini_analyzer  # 🆕 NEW
        self.subtitle = subtitle_service
        self.video = video_service
        self.progress = progress_repo
        self.history = history_repo
    
    def process(self, video_id: str, youtube_url: str, clip_duration: int, 
                range_percent: str, generate_mode: str = "audio",
                total_clips: int = 5):
        """Main processing pipeline with mode selection"""
        try:
            
            total_clips = max(MIN_CLIPS_COUNT, min(MAX_CLIPS_COUNT, total_clips))
            logger.info(f"🎯 Generation Mode: {generate_mode.upper()} | Clips: {total_clips}")

            
            self.progress.update(video_id, "validating", 5, "Validating YouTube video...")
            video_info = self.youtube.get_video_info(youtube_url)
            total_duration = video_info['duration']
            
            
            if total_duration > MAX_DURATION_SECONDS:
                raise Exception(f"Video too long: {total_duration}s (max: {MAX_DURATION_SECONDS}s)")
            
            logger.info(f"Video: {video_info['title']} - {total_duration}s")
            logger.info(f"🎯 Generation Mode: {generate_mode.upper()}")
            
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
            
            # 🆕 Step 5: MODE SELECTION - Audio / Context / Viral
            # In VideoProcessor.process() method, viral mode section:

            if generate_mode == "viral":
                # 🔥 VIRAL MODE: Context-aware Gemini analysis
                if not self.gemini:
                    raise Exception("Gemini Viral Analyzer not available. Check GEMINI_API_KEY.")
                
                self.progress.update(video_id, "analyzing", 40, 
                    f"🔥 Analyzing with Gemini AI ({total_clips} clips)...")
                
                # Prepare transcript
                transcript_segments = [
                    {
                        'start': seg['start'],
                        'end': seg['end'],
                        'text': seg['text']
                    }
                    for seg in result.get('segments', [])
                ]
                
                # 🆕 Call Gemini with video context
                viral_result = self.gemini.analyze_viral_segments(
                    youtube_url=youtube_url,
                    video_title=video_info.get('title', 'Unknown'),           # 🆕 NEW
                    video_description=video_info.get('description', ''),      # 🆕 NEW
                    video_duration=actual_duration,
                    transcript=transcript_segments,
                    language="id",
                    clip_duration=clip_duration,
                    max_retries=GEMINI_MAX_RETRIES,
                    timeout=GEMINI_TIMEOUT,
                    total_clips=total_clips
                )
                
                # Log theme analysis
                if 'video_theme_analysis' in viral_result:
                    logger.info(f"📊 Video Theme: {viral_result['video_theme_analysis']}")
                
                self.progress.update(video_id, "selecting_clips", 50, 
                                f"Selecting top {total_clips} theme-relevant clips...")
                
                # Convert to clipper format
                gemini_clips = self.gemini.format_for_clipper(viral_result)
                top_clips = self.clip.find_top_clips_by_viral(gemini_clips,total_clips)    
            elif generate_mode == "context":
            # CONTEXT MODE
                self.progress.update(video_id, "analyzing", 40, 
                                f"Analyzing conversation context ({total_clips} clips)...")
                
                analyzed_segments = self.context.analyze_transcript_for_clips(
                    result, clip_duration, CONTEXT_DURATION_FLEX
                )
                
                self.progress.update(video_id, "selecting_clips", 50, 
                                f"Selecting top {total_clips} clips...")
                
                top_clips = self.clip.find_top_clips_by_context(
                    analyzed_segments, total_clips  # 🆕 Pass count
                )
                
            else:
                # AUDIO MODE: Engagement-based (original)
                self.progress.update(video_id, "analyzing", 40, 
                               f"Analyzing audio ({total_clips} clips)...")
            
                engagement_windows = self.audio.analyze_engagement(audio_path)
                
                self.progress.update(video_id, "selecting_clips", 50, 
                                f"Selecting top {total_clips} clips...")
                
                top_clips = self.clip.find_top_clips(
                    engagement_windows, clip_duration, total_clips  # 🆕 Pass count
                )
                
            # Rest of processing remains the same...
            clips_output = self._process_clips(
                video_id, youtube_url, top_clips, clip_duration, 
                range_start, result, generate_mode
            )
            
            # Step 8: Finalize
            self.progress.update(video_id, "finalizing", 95, "Finalizing...")
            self._save_metadata(
                video_id, youtube_url, video_info, range_percent, 
                range_start, range_end, actual_duration, clips_output, generate_mode  # 🆕 Pass mode
            )
            
            # Save history
            self.history.save(video_id, video_info, clips_output, range_percent)
            
            # Cleanup
            self._cleanup(video_id)
            
            # Complete
            mode_label = "context-based" if generate_mode == "context" else \
                        "viral" if generate_mode == "viral" else "audio-based"
            self.progress.update(video_id, "completed", 100, 
                                f"Completed! {len(clips_output)} {mode_label} clips ready")
            self.progress.add_metadata(
                video_id,
                clips=clips_output,
                video_info=video_info,
                range_percent=range_percent,
                total_clips=len(clips_output),
                generate_mode=generate_mode
            )
        
            logger.info(f"Processing completed for {video_id}: {len(clips_output)}/{total_clips} clips")
        
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            self.progress.update(video_id, "error", 0, str(e))
    
    def _process_clips(self, video_id: str, youtube_url: str, top_clips: List[dict], 
                  clip_duration: int, range_start: float, transcription_result: dict,
                  generate_mode: str = "audio") -> List[dict]:
        """Process each individual clip"""
        clips_output = []
        total_clips = len(top_clips)
        
        for idx, clip_info in enumerate(top_clips):
            # Calculate progress: 50-90% range divided by clip count
            progress_range = 40  # 90 - 50 = 40
            progress_per_clip = progress_range / total_clips
            progress = 50 + int((idx + 1) * progress_per_clip)
            
            self.progress.update(video_id, "processing_clip", progress, 
                            f"Processing clip {idx + 1}/{total_clips}...")
            
            clip_id = f"{video_id}_clip_{idx + 1}"
            
            # Calculate absolute times
            clip_start_in_range = clip_info['start']
            clip_end_in_range = clip_info['end']
            absolute_clip_start = range_start + clip_start_in_range
            absolute_clip_end = range_start + clip_end_in_range
            
            # Actual duration
            actual_clip_duration = int(clip_end_in_range - clip_start_in_range)
            
            # Download video clip
            raw_clip_path = CLIPS_DIR / f"{clip_id}_raw.mp4"
            
            if not self.youtube.download_video_clip(youtube_url, absolute_clip_start, 
                                                    actual_clip_duration, raw_clip_path):
                if not self.youtube.extract_clip_with_ffmpeg(youtube_url, absolute_clip_start, 
                                                            actual_clip_duration, raw_clip_path):
                    logger.warning(f"Failed to download clip {idx + 1}, skipping...")
                    continue
            
            # Extract words for subtitle
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
            clip_data = {
                "clip_id": clip_id,
                "clip_number": idx + 1,
                "start_time": absolute_clip_start,
                "end_time": absolute_clip_end,
                "duration": actual_clip_duration,
                "engagement_score": clip_info['engagement_score'],
                "output_file": str(output_path),
                "word_count": len(clip_words)
            }
            
            # Add mode-specific metadata
            if generate_mode == "context":
                clip_data["context_reason"] = clip_info.get('context_reason', 'Valuable segment')
                clip_data["text_preview"] = clip_info.get('text_preview', '')
            
            elif generate_mode == "viral":
                # 🆕 Add viral-specific metadata
                clip_data["viral_category"] = clip_info.get('viral_category', 'value')
                clip_data["hook_text"] = clip_info.get('hook_text', '')
                clip_data["suggested_caption"] = clip_info.get('suggested_caption', '')
                clip_data["loop_hint"] = clip_info.get('loop_hint', 'N/A')
                clip_data["reason"] = clip_info.get('reason', 'Selected by Gemini')
            
            clips_output.append(clip_data)
    
        return clips_output
    
    def _save_metadata(self, video_id: str, youtube_url: str, video_info: dict, 
                      range_percent: str, range_start: float, range_end: float, 
                      actual_duration: float, clips: List[dict], 
                      generate_mode: str = "audio"):  # 🆕 NEW parameter
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
            "generate_mode": generate_mode,  # 🆕 NEW
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
            "🆕 TWO GENERATION MODES:",
            "  - Audio Mode: Engagement-based (sound intensity)",
            "  - Context Mode: Semantic-based (conversation meaning)",
            "Top 5 clips with burned subtitles",
            "Max duration: 2 hours"
        ],
        "endpoints": {
            "POST /process": "Process YouTube video (add generate_mode: 'audio' | 'context')",
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
        
        total_clips = request.total_clips or TOP_CLIPS_COUNT
        if total_clips < MIN_CLIPS_COUNT or total_clips > MAX_CLIPS_COUNT:
            raise HTTPException(
                status_code=400,
                detail=f"total_clips must be between {MIN_CLIPS_COUNT} and {MAX_CLIPS_COUNT}"
            )
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
        
        # 🆕 Validate generate_mode
        generate_mode = request.generate_mode or "audio"
        if generate_mode not in ["audio", "context", "viral"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid generate_mode. Use 'audio' or 'context'"
            )
        
        # Generate video ID
        video_id = str(uuid.uuid4())
        
        # Initialize progress
        mode_label = "context-based" if generate_mode == "context" else "audio-based"
        progress_repo.update(video_id, "queued", 0, f"Video queued for {mode_label} processing")
        
        # Start processing in background
        background_tasks.add_task(
            video_processor.process,
            video_id,
            request.youtube_url,
            request.clip_duration or CLIP_DURATION,
            request.range_percent or "0-100",
            generate_mode,  # 🆕 Pass mode
            total_clips
        )
        
        return {
            "status": "processing",
            "video_id": video_id,
            "range_percent": request.range_percent or "0-100",
            "generate_mode": generate_mode,  # 🆕 NEW
            "total_clips": total_clips,
            "message": f"Processing started in {mode_label} mode. Use /progress/{{video_id}} to check status"
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
    
@app.get("/history/videos")
async def get_all_videos():
    """
    Get all videos from output folder
    Reads all metadata files and returns complete video list
    """
    try:
        videos = output_history_service.get_all_videos()
        
        return {
            "total": len(videos),
            "videos": videos
        }
        
    except Exception as e:
        logger.error(f"Error loading videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/videos/{video_id}")
async def get_video_detail(video_id: str):
    """Get detailed information for specific video"""
    try:
        video = output_history_service.get_video_by_id(video_id)
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return video
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/videos/{video_id}")
async def delete_video(video_id: str):
    """Delete video and all its clips"""
    try:
        success = output_history_service.delete_video(video_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete video")
        
        return {
            "status": "success",
            "message": f"Video {video_id} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/stats")
async def get_storage_stats():
    """Get storage statistics"""
    try:
        stats = output_history_service.get_storage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)