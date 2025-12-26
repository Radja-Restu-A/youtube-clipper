from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import whisper
import os
import json
import uuid
from pathlib import Path
import logging
from typing import Dict, List, Optional
from datetime import datetime
import subprocess
import shutil
import yt_dlp
import librosa
import numpy as np
from scipy.signal import find_peaks

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Subtitle API with Auto Clip")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
CLIPS_DIR = BASE_DIR / "clips"
SUBTITLES_DIR = BASE_DIR / "subtitles"
OUTPUT_DIR = BASE_DIR / "output"
HISTORY_DIR = BASE_DIR / "history"
TEMP_DIR = BASE_DIR / "temp"

# Create directories
for dir_path in [AUDIO_DIR, CLIPS_DIR, SUBTITLES_DIR, OUTPUT_DIR, HISTORY_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True)

# Progress tracking
transcribe_progress: Dict[str, dict] = {}

# Load Whisper model
MODEL_NAME = "small"

# Auto-detect GPU
import torch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")

if DEVICE == "cuda":
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"CUDA Version: {torch.version.cuda}")

logger.info(f"Loading Whisper model: {MODEL_NAME}")
model = whisper.load_model(MODEL_NAME, device=DEVICE)
logger.info("Model loaded successfully")

# Constants
MAX_DURATION_SECONDS = 7200  # 2 hours
CLIP_DURATION = 45  # seconds per clip
TOP_CLIPS_COUNT = 5


class YouTubeRequest(BaseModel):
    youtube_url: str
    clip_duration: Optional[int] = 45
    range_percent: Optional[str] = "0-100"  # NEW: Range selector


def update_progress(video_id: str, status: str, progress: int, message: str = ""):
    """Update progress for a video transcription"""
    transcribe_progress[video_id] = {
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    logger.info(f"Progress update for {video_id}: {status} ({progress}%) - {message}")


def parse_range_percent(range_str: str, total_duration: float) -> tuple:
    """
    Parse range percentage string and convert to seconds
    Examples:
    - "0-25" with 3600s duration → (0, 900)
    - "26-50" with 3600s duration → (936, 1800)
    - "51-75" with 3600s duration → (1836, 2700)
    - "76-100" with 3600s duration → (2736, 3600)
    """
    try:
        start_percent, end_percent = map(int, range_str.split('-'))
        
        # Validate range
        if not (0 <= start_percent < end_percent <= 100):
            raise ValueError("Invalid range: start must be < end, both in 0-100")
        
        start_seconds = (start_percent / 100) * total_duration
        end_seconds = (end_percent / 100) * total_duration
        
        logger.info(f"Range {range_str}% → {start_seconds:.1f}s to {end_seconds:.1f}s")
        
        return start_seconds, end_seconds
        
    except Exception as e:
        logger.error(f"Error parsing range: {e}")
        raise ValueError(f"Invalid range format. Use format like '0-25', '26-50', etc.")


def get_youtube_info(url: str) -> dict:
    """Get YouTube video information without downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'channel': info.get('uploader', 'Unknown'),
                'thumbnail': info.get('thumbnail', '')
            }
    except Exception as e:
        logger.error(f"Error getting YouTube info: {str(e)}")
        raise Exception(f"Failed to get video info: {str(e)}")


def download_youtube_audio_range(url: str, output_path: Path, video_id: str, 
                                 start_time: float = None, end_time: float = None) -> Path:
    """
    Download audio from YouTube with optional time range
    If start_time and end_time are provided, only download that section
    """
    logger.info(f"Downloading audio from: {url}")
    if start_time is not None and end_time is not None:
        logger.info(f"Time range: {start_time:.1f}s to {end_time:.1f}s")
    
    audio_file = output_path / f"{video_id}.mp3"
    
    # Base options for audio download
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_path / f'{video_id}_temp.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        # Download full audio first (we need this for analysis)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        temp_audio = output_path / f"{video_id}_temp.mp3"
        
        # If range is specified, trim the audio
        if start_time is not None and end_time is not None:
            logger.info(f"Trimming audio to range: {start_time:.1f}s - {end_time:.1f}s")
            
            cmd = [
                'ffmpeg',
                '-i', str(temp_audio),
                '-ss', str(start_time),
                '-to', str(end_time),
                '-c', 'copy',
                '-y',
                str(audio_file)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Remove temp file
            if temp_audio.exists():
                temp_audio.unlink()
        else:
            # No range specified, just rename
            temp_audio.rename(audio_file)
        
        if not audio_file.exists():
            raise Exception("Audio file not created")
        
        logger.info(f"Audio downloaded: {audio_file}")
        return audio_file
        
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise Exception(f"Failed to download audio: {str(e)}")


def analyze_audio_engagement(audio_path: Path) -> List[dict]:
    """
    Analyze audio to find most engaging segments based on:
    - Audio energy/intensity
    - Speech rate
    - Volume changes
    Returns list of segments with engagement scores
    """
    logger.info(f"Analyzing audio engagement: {audio_path}")
    
    try:
        # Load audio
        y, sr = librosa.load(str(audio_path), sr=22050)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Calculate features in windows
        window_size = 5  # seconds
        hop_size = 1  # seconds
        
        windows = []
        for start in np.arange(0, duration - window_size, hop_size):
            end = start + window_size
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            
            window_audio = y[start_sample:end_sample]
            
            # Feature 1: RMS Energy (loudness)
            rms = np.sqrt(np.mean(window_audio**2))
            
            # Feature 2: Zero Crossing Rate (speech activity indicator)
            zcr = np.mean(librosa.zero_crossings(window_audio))
            
            # Feature 3: Spectral Centroid (tonal quality)
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=window_audio, sr=sr))
            
            # Feature 4: Tempo/Beat strength
            onset_env = librosa.onset.onset_strength(y=window_audio, sr=sr)
            tempo_strength = np.mean(onset_env)
            
            # Combined engagement score (normalized)
            engagement_score = (
                rms * 0.4 +  # Energy is most important
                zcr * 0.2 +  # Speech activity
                (spectral_centroid / 5000) * 0.2 +  # Tonal quality (normalized)
                tempo_strength * 0.2  # Rhythm/dynamics
            )
            
            windows.append({
                'start': start,
                'end': end,
                'engagement_score': float(engagement_score),
                'rms': float(rms),
                'zcr': float(zcr)
            })
        
        logger.info(f"Analyzed {len(windows)} windows")
        return windows
        
    except Exception as e:
        logger.error(f"Error analyzing audio: {str(e)}")
        raise Exception(f"Failed to analyze audio: {str(e)}")


def find_top_clips(engagement_windows: List[dict], clip_duration: int, top_n: int = 5) -> List[dict]:
    """
    Find top N clips based on engagement scores
    Ensures clips don't overlap
    """
    logger.info(f"Finding top {top_n} clips of {clip_duration}s duration")
    
    # Sort by engagement score
    sorted_windows = sorted(engagement_windows, key=lambda x: x['engagement_score'], reverse=True)
    
    selected_clips = []
    used_ranges = []
    
    for window in sorted_windows:
        if len(selected_clips) >= top_n:
            break
        
        clip_start = window['start']
        clip_end = clip_start + clip_duration
        
        # Check if this clip overlaps with already selected clips
        overlap = False
        for used_start, used_end in used_ranges:
            if not (clip_end <= used_start or clip_start >= used_end):
                overlap = True
                break
        
        if not overlap:
            selected_clips.append({
                'clip_id': len(selected_clips) + 1,
                'start': clip_start,
                'end': clip_end,
                'duration': clip_duration,
                'engagement_score': window['engagement_score']
            })
            used_ranges.append((clip_start, clip_end))
    
    # Sort by start time
    selected_clips.sort(key=lambda x: x['start'])
    
    logger.info(f"Selected {len(selected_clips)} clips")
    return selected_clips


def download_video_clip(url: str, start_time: float, duration: float, output_path: Path) -> bool:
    """Download specific clip from YouTube video using yt-dlp"""
    logger.info(f"Downloading clip: {start_time}s - {start_time + duration}s")
    
    ydl_opts = {
        'format': 'best[height<=1080]',
        'outtmpl': str(output_path),
        'quiet': False,
        'no_warnings': False,
        'download_ranges': lambda info_dict, ydl: [{
            'start_time': start_time,
            'end_time': start_time + duration
        }],
        'force_keyframes_at_cuts': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        logger.error(f"Error downloading clip: {str(e)}")
        return False


def extract_clip_with_ffmpeg(url: str, start_time: float, duration: float, output_path: Path) -> bool:
    """Fallback method: Use ffmpeg to extract clip from streaming"""
    logger.info(f"Extracting clip with FFmpeg: {start_time}s - {duration}s")
    
    try:
        # Get best video URL using yt-dlp
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info['url']
        
        # Use ffmpeg to extract clip
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', video_url,
            '-t', str(duration),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'medium',
            '-crf', '23',
            '-y',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Clip extracted successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"FFmpeg extraction failed: {str(e)}")
        return False

import re

def clean_subtitle_text(text: str) -> str:
    """
    Remove unwanted punctuation that breaks subtitle readability.
    """
    # Hapus karakter -, . , 
    text = re.sub(r"[-\.,]", "", text)

    # Rapikan spasi berlebih
    text = re.sub(r"\s+", " ", text)

    return text.strip()



def create_ass_subtitle(words: List[dict], ass_path: Path):
    """Create ASS subtitle with Opus Clip style - ALL UPPERCASE"""
    
    ass_content = """[Script Info]
Title: Opus Clip Style Subtitle
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Group words into lines (max 6 words per line)
    lines = []
    current_line = []
    
    for i, word in enumerate(words):
        current_line.append(word)
        if len(current_line) >= 6 or i == len(words) - 1:
            if current_line:
                lines.append(current_line)
                current_line = []
    
    # Generate subtitle events
    for line_words in lines:
        if not line_words:
            continue
        
        for word_idx, word in enumerate(line_words):
            text_parts = []
            
            for i, w in enumerate(line_words):
                word_upper = w['word'].strip().upper()
                
                if i == word_idx:
                    text_parts.append(f"{{\\c&H00FF00&\\b1}}{word_upper}{{\\c&HFFFFFF&\\b0}}")
                else:
                    text_parts.append(word_upper)
            
            full_text = " ".join(text_parts)
            start_time = format_ass_time(word['start'])
            end_time = format_ass_time(word['end'])
            
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{full_text}\n"
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    logger.info(f"ASS subtitle created: {ass_path}")


def format_ass_time(seconds: float) -> str:
    """Format seconds to ASS time format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"


def burn_subtitle_to_video(video_path: Path, ass_path: Path, output_path: Path):
    """Burn ASS subtitle into video"""
    logger.info(f"Burning subtitle to video: {output_path}")
    
    temp_ass = video_path.parent / "temp_subtitle.ass"
    shutil.copy(ass_path, temp_ass)
    
    try:
        cmd = [
            'ffmpeg',
            '-i', str(video_path.absolute()),
            '-vf', f"ass={temp_ass.name}",
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            str(output_path.absolute())
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(video_path.parent))
        logger.info("Subtitle burned successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        raise Exception(f"Failed to burn subtitle: {e.stderr}")
    finally:
        if temp_ass.exists():
            temp_ass.unlink()


def cleanup_temp_files(video_id: str):
    """Clean up temporary files"""
    logger.info(f"Cleaning up temporary files for {video_id}")
    
    patterns = [
        AUDIO_DIR / f"{video_id}.*",
        CLIPS_DIR / f"{video_id}_clip_*_raw.*",
        TEMP_DIR / f"{video_id}*"
    ]
    
    for pattern in patterns:
        for file in pattern.parent.glob(pattern.name):
            try:
                file.unlink()
                logger.info(f"Deleted: {file}")
            except Exception as e:
                logger.warning(f"Could not delete {file}: {e}")


def save_to_history(video_id: str, video_info: dict, clips: List[dict], range_used: str):
    """Save processing history"""
    history_file = HISTORY_DIR / "history.json"
    
    history = []
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    history_entry = {
        "video_id": video_id,
        "title": video_info.get('title', 'Unknown'),
        "channel": video_info.get('channel', 'Unknown'),
        "date": datetime.now().isoformat(),
        "duration": video_info.get('duration', 0),
        "range_used": range_used,
        "clips_count": len(clips),
        "status": "completed"
    }
    
    history.insert(0, history_entry)
    history = history[:100]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def process_youtube_video_task(video_id: str, youtube_url: str, clip_duration: int, range_percent: str):
    """Main background task for YouTube video processing with range support"""
    try:
        # Step 1: Get video info and validate duration
        update_progress(video_id, "validating", 5, "Validating YouTube video...")
        
        video_info = get_youtube_info(youtube_url)
        total_duration = video_info['duration']
        
        if total_duration > MAX_DURATION_SECONDS:
            raise Exception(f"Video too long: {total_duration}s (max: {MAX_DURATION_SECONDS}s / 2 hours)")
        
        logger.info(f"Video info: {video_info['title']} - {total_duration}s")
        
        # Step 2: Parse range
        range_start, range_end = parse_range_percent(range_percent, total_duration)
        actual_duration = range_end - range_start
        
        logger.info(f"Processing range: {range_percent}% ({range_start:.1f}s - {range_end:.1f}s)")
        
        # Step 3: Download audio with range
        update_progress(video_id, "downloading_audio", 10, 
                       f"Downloading audio (range: {range_percent}%)...")
        
        audio_path = download_youtube_audio_range(
            youtube_url, 
            AUDIO_DIR, 
            video_id,
            range_start,
            range_end
        )
        
        # Step 4: Transcribe audio
        update_progress(video_id, "transcribing", 20, "Transcribing audio with Whisper AI...")
        
        result = model.transcribe(
            str(audio_path),
            language="id",
            word_timestamps=True,
            verbose=True,
            fp16=torch.cuda.is_available()
        )
        
        # Step 5: Analyze audio engagement
        update_progress(video_id, "analyzing", 40, "Analyzing audio for best clips...")
        engagement_windows = analyze_audio_engagement(audio_path)
        
        # Step 6: Find top clips
        update_progress(video_id, "selecting_clips", 50, f"Selecting top {TOP_CLIPS_COUNT} clips...")
        top_clips = find_top_clips(engagement_windows, clip_duration, TOP_CLIPS_COUNT)
        
        # Step 7: Process each clip
        clips_output = []
        for idx, clip_info in enumerate(top_clips):
            progress = 50 + (idx * 8)
            update_progress(video_id, "processing_clip", progress, 
                          f"Processing clip {idx + 1}/{len(top_clips)}...")
            
            clip_id = f"{video_id}_clip_{idx + 1}"
            
            # IMPORTANT: Adjust clip times to absolute position in original video
            clip_start_in_range = clip_info['start']
            clip_end_in_range = clip_info['end']
            
            # Convert to absolute time in original video
            absolute_clip_start = range_start + clip_start_in_range
            absolute_clip_end = range_start + clip_end_in_range
            
            # Download video clip from absolute position
            raw_clip_path = CLIPS_DIR / f"{clip_id}_raw.mp4"
            
            # Try yt-dlp first, fallback to ffmpeg
            if not download_video_clip(youtube_url, absolute_clip_start, clip_duration, raw_clip_path):
                if not extract_clip_with_ffmpeg(youtube_url, absolute_clip_start, clip_duration, raw_clip_path):
                    logger.warning(f"Failed to download clip {idx + 1}, skipping...")
                    continue
            
            # Extract words for this clip (relative to the trimmed audio)
            clip_words = []
            for segment in result["segments"]:
                if "words" in segment:
                    for word_info in segment["words"]:
                        word_time = word_info["start"]
                        if clip_start_in_range <= word_time <= clip_end_in_range:
                            # Adjust time to be relative to clip start

                            clean_word = clean_subtitle_text(word_info["word"])

                            # skip kalau setelah dibersihkan kosong
                            if not clean_word:
                                continue

                            clip_words.append({
                                "word": clean_word.strip().upper(),
                                "start": round(word_info["start"] - clip_start_in_range, 2),
                                "end": round(word_info["end"] - clip_start_in_range, 2)
                            })
            
            # Create subtitle for clip
            ass_path = SUBTITLES_DIR / f"{clip_id}.ass"
            create_ass_subtitle(clip_words, ass_path)
            
            # Burn subtitle
            output_path = OUTPUT_DIR / f"{clip_id}_subtitled.mp4"
            burn_subtitle_to_video(raw_clip_path, ass_path, output_path)
            
            # Save clip info
            clips_output.append({
                "clip_id": clip_id,
                "clip_number": idx + 1,
                "start_time": absolute_clip_start,  # Absolute time in original video
                "end_time": absolute_clip_end,
                "duration": clip_duration,
                "engagement_score": clip_info['engagement_score'],
                "output_file": str(output_path),
                "word_count": len(clip_words)
            })
        
        # Step 8: Save metadata
        update_progress(video_id, "finalizing", 95, "Finalizing...")
        
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
            "total_clips": len(clips_output),
            "clips": clips_output,
            "processed_at": datetime.now().isoformat()
        }
        
        metadata_path = OUTPUT_DIR / f"{video_id}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Save to history
        save_to_history(video_id, video_info, clips_output, range_percent)
        
        # Cleanup temporary files
        cleanup_temp_files(video_id)
        
        # Update final progress
        update_progress(video_id, "completed", 100, 
                       f"Completed! {len(clips_output)} clips ready (range: {range_percent}%)")
        
        transcribe_progress[video_id].update({
            "clips": clips_output,
            "video_info": video_info,
            "range_percent": range_percent,
            "total_clips": len(clips_output)
        })
        
        logger.info(f"Processing completed for {video_id}")
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        update_progress(video_id, "error", 0, str(e))
        transcribe_progress[video_id]["error"] = str(e)


@app.get("/")
def read_root():
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
    """Process YouTube video - download audio, detect clips, add subtitles"""
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
                raise HTTPException(status_code=400, 
                                  detail="Invalid range_percent. Use format: '0-25', '26-50', '51-75', or '76-100'")
        
        # Generate video ID
        video_id = str(uuid.uuid4())
        
        # Initialize progress
        update_progress(video_id, "queued", 0, "Video queued for processing")
        
        # Start processing in background
        background_tasks.add_task(
            process_youtube_video_task,
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
        
    except Exception as e:
        logger.error(f"Error starting process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/progress/{video_id}")
async def get_progress(video_id: str):
    """Get processing progress"""
    if video_id not in transcribe_progress:
        raise HTTPException(status_code=404, detail="Video ID not found")
    
    return transcribe_progress[video_id]


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
        history_file = HISTORY_DIR / "history.json"
        
        if not history_file.exists():
            return {"history": []}
        
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Error loading history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)