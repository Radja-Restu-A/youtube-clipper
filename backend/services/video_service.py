import subprocess
import shutil
from pathlib import Path

class VideoProcessingService:
    @staticmethod
    def burn_subtitle(video_path: Path, ass_path: Path, output_path: Path):
        """Burn ASS subtitle into video"""
        from config import logger
        
        logger.info(f"Burning subtitle to video: {output_path}")
        
        temp_ass = video_path.parent / "temp_subtitle.ass"
        shutil.copy(ass_path, temp_ass)
        
        try:
            cmd = [
                'ffmpeg', '-i', str(video_path.absolute()),
                '-vf', f"ass={temp_ass.name}",
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-c:a', 'copy', '-y', str(output_path.absolute())
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True, 
                         cwd=str(video_path.parent))
            logger.info("Subtitle burned successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise Exception(f"Failed to burn subtitle: {e.stderr}")
        finally:
            if temp_ass.exists():
                temp_ass.unlink()