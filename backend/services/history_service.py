# ============================================
# Backend: Output-Based History System
# ============================================

# 1. services/history_service.py
# ============================================

from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime
import os

class OutputHistoryService:
    """Service untuk membaca history dari folder output"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def get_all_videos(self) -> List[Dict]:
        """
        Scan folder output dan baca semua file metadata
        Returns list of video metadata sorted by processed_at (newest first)
        """
        videos = []
        
        if not self.output_dir.exists():
            return videos
        
        # Cari semua file metadata JSON
        for metadata_file in self.output_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Extract video_id dari filename
                video_id = metadata_file.stem.replace('_metadata', '')
                
                # Cek apakah clips masih ada
                available_clips = []
                for clip in metadata.get('clips', []):
                    clip_file = Path(clip.get('output_file', ''))
                    if clip_file.exists():
                        # Add file size info
                        file_size = os.path.getsize(clip_file)
                        clip_with_size = {**clip, 'file_size': file_size}
                        available_clips.append(clip_with_size)
                
                # Build video entry
                video_entry = {
                    'video_id': video_id,
                    'title': metadata.get('video_info', {}).get('title', 'Unknown'),
                    'channel': metadata.get('video_info', {}).get('channel', 'Unknown'),
                    'thumbnail': metadata.get('video_info', {}).get('thumbnail', ''),
                    'duration': metadata.get('video_info', {}).get('duration', 0),
                    'youtube_url': metadata.get('youtube_url', ''),
                    'range_percent': metadata.get('range_percent', '0-100'),
                    'range_seconds': metadata.get('range_seconds', {}),
                    'total_clips': len(available_clips),
                    'clips': available_clips,
                    'processed_at': metadata.get('processed_at', ''),
                    'metadata_file': str(metadata_file)
                }
                
                videos.append(video_entry)
                
            except Exception as e:
                print(f"Error reading {metadata_file}: {e}")
                continue
        
        # Sort by processed_at (newest first)
        videos.sort(key=lambda x: x.get('processed_at', ''), reverse=True)
        
        return videos
    
    def get_video_by_id(self, video_id: str) -> Optional[Dict]:
        """Get specific video metadata by video_id"""
        metadata_file = self.output_dir / f"{video_id}_metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Check available clips
            available_clips = []
            for clip in metadata.get('clips', []):
                clip_file = Path(clip.get('output_file', ''))
                if clip_file.exists():
                    file_size = os.path.getsize(clip_file)
                    clip_with_size = {**clip, 'file_size': file_size}
                    available_clips.append(clip_with_size)
            
            metadata['clips'] = available_clips
            metadata['total_clips'] = len(available_clips)
            
            return metadata
            
        except Exception as e:
            print(f"Error reading video {video_id}: {e}")
            return None
    
    def delete_video(self, video_id: str) -> bool:
        """Delete all files related to a video"""
        try:
            deleted_files = []
            
            # Delete metadata
            metadata_file = self.output_dir / f"{video_id}_metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
                deleted_files.append(str(metadata_file))
            
            # Delete all clip files
            for clip_file in self.output_dir.glob(f"{video_id}_clip_*_subtitled.mp4"):
                if clip_file.exists():
                    clip_file.unlink()
                    deleted_files.append(str(clip_file))
            
            # Delete subtitle files
            from config import SUBTITLES_DIR
            for subtitle_file in SUBTITLES_DIR.glob(f"{video_id}_clip_*.ass"):
                if subtitle_file.exists():
                    subtitle_file.unlink()
                    deleted_files.append(str(subtitle_file))
            
            print(f"Deleted {len(deleted_files)} files for video {video_id}")
            return True
            
        except Exception as e:
            print(f"Error deleting video {video_id}: {e}")
            return False
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        total_videos = 0
        total_clips = 0
        total_size = 0
        
        for metadata_file in self.output_dir.glob("*_metadata.json"):
            total_videos += 1
            
            # Count clips
            video_id = metadata_file.stem.replace('_metadata', '')
            for clip_file in self.output_dir.glob(f"{video_id}_clip_*_subtitled.mp4"):
                if clip_file.exists():
                    total_clips += 1
                    total_size += os.path.getsize(clip_file)
        
        return {
            'total_videos': total_videos,
            'total_clips': total_clips,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2)
        }
