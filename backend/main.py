from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import whisper
import os
import json
import uuid
from pathlib import Path
import logging
from typing import Dict, List
from datetime import datetime
import subprocess
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Subtitle API with Opus Clip Style")

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
VIDEOS_DIR = BASE_DIR / "videos"
SUBTITLES_DIR = BASE_DIR / "subtitles"
OUTPUT_DIR = BASE_DIR / "output"
HISTORY_DIR = BASE_DIR / "history"

# Create directories if not exist
VIDEOS_DIR.mkdir(exist_ok=True)
SUBTITLES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)

# Progress tracking
transcribe_progress: Dict[str, dict] = {}

# Load Whisper model
MODEL_NAME = "large-v3"

# Auto-detect GPU
import torch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")

if DEVICE == "cuda":
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"CUDA Version: {torch.version.cuda}")
else:
    logger.info("No GPU detected, using CPU")

logger.info(f"Loading Whisper model: {MODEL_NAME}")
model = whisper.load_model(MODEL_NAME, device=DEVICE)
logger.info("Model loaded successfully")


class TranscribeRequest(BaseModel):
    video_id: str


def update_progress(video_id: str, status: str, progress: int):
    """Update progress for a video transcription"""
    transcribe_progress[video_id] = {
        "status": status,
        "progress": progress,
        "timestamp": datetime.now().isoformat()
    }
    logger.info(f"Progress update for {video_id}: {status} ({progress}%)")


def create_ass_subtitle(words: List[dict], ass_path: Path):
    """Create ASS subtitle with Opus Clip style (per-word highlight animation) - ALL UPPERCASE"""
    
    # ASS Header dengan style yang mirip Opus Clip
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
Style: Highlight,Montserrat,72,&H0000FF00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Group words into lines (max 6-8 words per line for readability)
    lines = []
    current_line = []
    
    for i, word in enumerate(words):
        current_line.append(word)
        
        # Create new line every 6 words or at the end
        if len(current_line) >= 6 or i == len(words) - 1:
            if current_line:
                lines.append(current_line)
                current_line = []
    
    # Generate subtitle events with per-word highlighting
    for line_idx, line_words in enumerate(lines):
        if not line_words:
            continue
            
        line_start = line_words[0]['start']
        line_end = line_words[-1]['end']
        
        # For each word in the line, create highlight effect
        for word_idx, word in enumerate(line_words):
            # Build the text with proper highlighting
            text_parts = []
            
            for i, w in enumerate(line_words):
                # Convert word to UPPERCASE - FIX BUG DISINI
                word_upper = w['word'].strip().upper()
                
                if i == word_idx:
                    # Current word - highlighted in green with bold
                    text_parts.append(f"{{\\c&H00FF00&\\b1}}{word_upper}{{\\c&HFFFFFF&\\b0}}")
                else:
                    # Other words - white
                    text_parts.append(word_upper)
            
            full_text = " ".join(text_parts)
            
            # Format time
            start_time = format_ass_time(word['start'])
            end_time = format_ass_time(word['end'])
            
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{full_text}\n"
    
    # Write ASS file
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    logger.info(f"ASS subtitle created: {ass_path}")


def format_ass_time(seconds: float) -> str:
    """Format seconds to ASS time format (H:MM:SS.CC)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"


def burn_subtitle_to_video(video_path: Path, ass_path: Path, output_path: Path):
    """Burn ASS subtitle into video using FFmpeg"""
    logger.info(f"Burning subtitle to video: {output_path}")
    
    # Copy subtitle to same directory as video with simple name
    temp_ass = video_path.parent / "temp_subtitle.ass"
    shutil.copy(ass_path, temp_ass)
    
    try:
        # FFmpeg command with ASS subtitle filter
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
        
        logger.info(f"FFmpeg command: {' '.join(cmd)}")
        
        # Run FFmpeg from video directory
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(video_path.parent)
        )
        logger.info("Subtitle burned successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg stdout: {e.stdout}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        raise Exception(f"Failed to burn subtitle: {e.stderr}")
    finally:
        # Clean up temp file
        if temp_ass.exists():
            temp_ass.unlink()


def save_to_history(video_id: str, video_filename: str, total_words: int, duration: float):
    """Save video processing history"""
    history_file = HISTORY_DIR / "history.json"
    
    # Load existing history
    history = []
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    # Add new entry
    history_entry = {
        "video_id": video_id,
        "filename": video_filename,
        "date": datetime.now().isoformat(),
        "total_words": total_words,
        "duration": round(duration, 2),
        "status": "completed"
    }
    
    history.insert(0, history_entry)  # Add to beginning
    
    # Keep only last 100 entries
    history = history[:100]
    
    # Save history
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    logger.info(f"History saved for {video_id}")


@app.get("/")
def read_root():
    return {
        "message": "Whisper Subtitle API with Opus Clip Style",
        "device": DEVICE,
        "model": MODEL_NAME,
        "style": "Per-word highlight animation (Opus Clip style) - ALL UPPERCASE",
        "endpoints": {
            "POST /upload": "Upload video file",
            "POST /transcribe": "Transcribe video and burn subtitle (async)",
            "GET /progress/{video_id}": "Get transcription progress",
            "GET /download/{video_id}": "Download video with burned subtitle",
            "GET /history": "Get processing history"
        }
    }


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file and save to local storage"""
    try:
        # Generate unique ID
        video_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = VIDEOS_DIR / f"{video_id}{file_extension}"
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Video uploaded: {file_path}")
        
        # Initialize progress
        transcribe_progress[video_id] = {
            "status": "uploaded",
            "progress": 0,
            "filename": file.filename,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "video_id": video_id,
            "filename": file.filename,
            "path": str(file_path)
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def transcribe_video_task(video_id: str):
    """Background task for video transcription and subtitle burning"""
    try:
        # Find video file
        video_files = list(VIDEOS_DIR.glob(f"{video_id}.*"))
        if not video_files:
            update_progress(video_id, "error", 0)
            return
        
        video_path = video_files[0]
        logger.info(f"Transcribing video: {video_path}")
        
        update_progress(video_id, "loading_audio", 10)
        
        # Transcribe with Whisper
        update_progress(video_id, "transcribing", 20)
        
        result = model.transcribe(
            str(video_path),
            language="id",
            word_timestamps=True,
            verbose=True,
            fp16=torch.cuda.is_available()
        )
        
        update_progress(video_id, "processing_words", 50)
        
        # Extract words with timestamps - UPPERCASE
        words = []
        for segment in result["segments"]:
            if "words" in segment:
                for word_info in segment["words"]:
                    words.append({
                        "word": word_info["word"].strip().upper(),  # UPPERCASE FIX
                        "start": round(word_info["start"], 2),
                        "end": round(word_info["end"], 2)
                    })
        
        update_progress(video_id, "creating_subtitle", 60)
        
        # Create ASS file with Opus Clip style
        ass_path = SUBTITLES_DIR / f"{video_id}.ass"
        create_ass_subtitle(words, ass_path)
        logger.info(f"ASS file created: {ass_path}")
        
        # Save JSON subtitle for reference - UPPERCASE
        subtitle_data = {
            "video_id": video_id,
            "language": "id",
            "words": words,
            "full_text": result["text"].upper()  # UPPERCASE FIX
        }
        
        json_path = SUBTITLES_DIR / f"{video_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(subtitle_data, f, ensure_ascii=False, indent=2)
        
        update_progress(video_id, "burning_subtitle", 70)
        
        # Burn subtitle to video
        output_path = OUTPUT_DIR / f"{video_id}_subtitled{video_path.suffix}"
        burn_subtitle_to_video(video_path, ass_path, output_path)
        
        # Get video duration (approximate from last word timestamp)
        duration = words[-1]['end'] if words else 0
        
        # Save to history
        filename = transcribe_progress[video_id].get("filename", "unknown")
        save_to_history(video_id, filename, len(words), duration)
        
        logger.info(f"Video with Opus Clip style subtitle created: {output_path}")
        logger.info(f"Total words: {len(words)}")
        
        update_progress(video_id, "completed", 100)
        
        # Store result
        transcribe_progress[video_id] = {
            "status": "completed",
            "progress": 100,
            "total_words": len(words),
            "output_file": str(output_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        transcribe_progress[video_id] = {
            "status": "error",
            "progress": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/transcribe")
async def transcribe_video(request: TranscribeRequest, background_tasks: BackgroundTasks):
    """Start transcription and subtitle burning in background"""
    try:
        video_id = request.video_id
        
        # Check if video exists
        video_files = list(VIDEOS_DIR.glob(f"{video_id}.*"))
        if not video_files:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Start transcription in background
        background_tasks.add_task(transcribe_video_task, video_id)
        
        return {
            "status": "processing",
            "video_id": video_id,
            "message": "Transcription started. Use /progress/{video_id} to check status"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription start error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/progress/{video_id}")
async def get_progress(video_id: str):
    """Get transcription progress"""
    if video_id not in transcribe_progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    
    return transcribe_progress[video_id]


@app.get("/download/{video_id}")
async def download_video(video_id: str):
    """Download video with burned subtitle"""
    try:
        # Check if processing is complete
        if video_id not in transcribe_progress:
            raise HTTPException(status_code=404, detail="Video not found")
        
        progress = transcribe_progress[video_id]
        
        if progress["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Video is not ready. Status: {progress['status']}")
        
        # Find output file
        output_files = list(OUTPUT_DIR.glob(f"{video_id}_subtitled.*"))
        if not output_files:
            raise HTTPException(status_code=404, detail="Output video not found")
        
        output_path = output_files[0]
        
        return FileResponse(
            path=str(output_path),
            filename=f"subtitled_{output_path.name}",
            media_type="video/mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/subtitle/{video_id}")
async def get_subtitle(video_id: str):
    """Get subtitle JSON by video ID"""
    try:
        json_path = SUBTITLES_DIR / f"{video_id}.json"
        
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Subtitle not found")
        
        with open(json_path, "r", encoding="utf-8") as f:
            subtitle_data = json.load(f)
        
        return subtitle_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading subtitle: {str(e)}")
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