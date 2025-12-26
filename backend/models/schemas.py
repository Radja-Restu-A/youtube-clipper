from pydantic import BaseModel
from typing import Optional, List, Dict

class YouTubeRequest(BaseModel):
    youtube_url: str
    clip_duration: Optional[int] = 45
    range_percent: Optional[str] = "0-100"
    generate_mode: Optional[str] = "audio"  # 🆕 NEW: "audio" | "context"

class ClipInfo(BaseModel):
    clip_id: str
    clip_number: int
    start_time: float
    end_time: float
    duration: int
    engagement_score: float
    output_file: str
    word_count: int
    context_reason: Optional[str] = None  # 🆕 NEW: Reason for context-based clips

class VideoMetadata(BaseModel):
    video_id: str
    youtube_url: str
    video_info: Dict
    range_percent: str
    range_seconds: Dict
    generate_mode: str  # 🆕 NEW: Track which mode was used
    total_clips: int
    clips: List[ClipInfo]
    processed_at: str

class ProgressUpdate(BaseModel):
    status: str
    progress: int
    message: str = ""
    timestamp: str