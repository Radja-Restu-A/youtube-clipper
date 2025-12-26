from typing import Dict
from datetime import datetime

class ProgressRepository:
    def __init__(self):
        self._progress_store: Dict[str, dict] = {}
    
    def update(self, video_id: str, status: str, progress: int, message: str = ""):
        """Update progress for a video"""
        from config import logger
        
        self._progress_store[video_id] = {
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Progress update for {video_id}: {status} ({progress}%) - {message}")
    
    def get(self, video_id: str) -> dict:
        """Get progress for a video"""
        return self._progress_store.get(video_id)
    
    def exists(self, video_id: str) -> bool:
        """Check if video_id exists"""
        return video_id in self._progress_store
    
    def add_metadata(self, video_id: str, **kwargs):
        """Add additional metadata to progress"""
        if video_id in self._progress_store:
            self._progress_store[video_id].update(kwargs)