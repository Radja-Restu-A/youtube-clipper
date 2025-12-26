import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class HistoryRepository:
    def __init__(self, history_dir: Path):
        self.history_file = history_dir / "history.json"
    
    def save(self, video_id: str, video_info: dict, clips: List[dict], range_used: str):
        """Save processing history"""
        history = self._load_history()
        
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
        history = history[:100]  # Keep last 100 entries
        
        self._save_history(history)
    
    def get_all(self) -> List[dict]:
        """Get all history entries"""
        return self._load_history()
    
    def _load_history(self) -> List[dict]:
        """Load history from file"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_history(self, history: List[dict]):
        """Save history to file"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
