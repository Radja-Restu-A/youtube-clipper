from pathlib import Path
import subprocess
from typing import Dict, Optional
import json

class LocalVideoService:
    """Service for processing locally uploaded videos"""
    
    @staticmethod
    def get_video_duration(video_path: Path) -> float:
        """Get video duration using ffprobe"""
        from config import logger
        
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                logger.info(f"Video duration: {duration:.2f}s")
                return duration
            else:
                raise Exception("Failed to get video duration")
                
        except Exception as e:
            logger.error(f"Error getting duration: {e}")
            return 0.0
    
    @staticmethod
    def extract_audio_from_video(video_path: Path, output_path: Path) -> bool:
        """Extract audio from video file"""
        from config import logger
        
        try:
            logger.info(f"Extracting audio from {video_path.name}...")
            
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-ar', '16000',  # 16kHz for Whisper
                '-ac', '1',  # Mono
                '-b:a', '128k',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"✅ Audio extracted: {output_path}")
                return True
            else:
                logger.error(f"❌ Audio extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return False
    
    @staticmethod
    def validate_video_file(video_path: Path) -> bool:
        """Validate if file is a valid video"""
        from config import logger
        
        if not video_path.exists():
            logger.error(f"File not found: {video_path}")
            return False
        
        # Check file extension
        valid_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}
        if video_path.suffix.lower() not in valid_extensions:
            logger.error(f"Invalid video format: {video_path.suffix}")
            return False
        
        # Check file size (max 2GB)
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        if video_path.stat().st_size > max_size:
            logger.error(f"File too large: {video_path.stat().st_size / 1024 / 1024:.2f}MB")
            return False
        
        return True