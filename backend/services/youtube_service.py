import yt_dlp
from pathlib import Path
import subprocess

class YouTubeService:
    @staticmethod
    def get_video_info(url: str) -> dict:
        """Get YouTube video information"""
        from config import logger
        
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
    
    @staticmethod
    def download_audio_range(url: str, output_path: Path, video_id: str, 
                            start_time: float = None, end_time: float = None) -> Path:
        """Download audio from YouTube with optional time range"""
        from config import logger
        
        logger.info(f"Downloading audio from: {url}")
        if start_time is not None and end_time is not None:
            logger.info(f"Time range: {start_time:.1f}s to {end_time:.1f}s")
        
        audio_file = output_path / f"{video_id}.mp3"
        
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
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            temp_audio = output_path / f"{video_id}_temp.mp3"
            
            if start_time is not None and end_time is not None:
                logger.info(f"Trimming audio to range: {start_time:.1f}s - {end_time:.1f}s")
                
                cmd = [
                    'ffmpeg', '-i', str(temp_audio),
                    '-ss', str(start_time), '-to', str(end_time),
                    '-c', 'copy', '-y', str(audio_file)
                ]
                
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                if temp_audio.exists():
                    temp_audio.unlink()
            else:
                temp_audio.rename(audio_file)
            
            if not audio_file.exists():
                raise Exception("Audio file not created")
            
            logger.info(f"Audio downloaded: {audio_file}")
            return audio_file
            
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            raise Exception(f"Failed to download audio: {str(e)}")
    
    @staticmethod
    def download_video_clip(url: str, start_time: float, duration: float, 
                           output_path: Path) -> bool:
        """Download specific clip from YouTube"""
        from config import logger
        
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
    
    @staticmethod
    def extract_clip_with_ffmpeg(url: str, start_time: float, duration: float, 
                                output_path: Path) -> bool:
        """Fallback: Use ffmpeg to extract clip"""
        from config import logger
        
        logger.info(f"Extracting clip with FFmpeg: {start_time}s - {duration}s")
        
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info['url']
            
            cmd = [
                'ffmpeg', '-ss', str(start_time), '-i', video_url,
                '-t', str(duration), '-c:v', 'libx264', '-c:a', 'aac',
                '-preset', 'medium', '-crf', '23', '-y', str(output_path)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Clip extracted successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"FFmpeg extraction failed: {str(e)}")
            return False
