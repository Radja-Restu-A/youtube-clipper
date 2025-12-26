from pydantic import BaseModel
from typing import Optional, List, Dict

class YouTubeRequest(BaseModel):
    youtube_url: str
    clip_duration: Optional[int] = 45
    range_percent: Optional[str] = "0-100"

class ClipInfo(BaseModel):
    clip_id: str
    clip_number: int
    start_time: float
    end_time: float
    duration: int
    engagement_score: float
    output_file: str
    word_count: int

class VideoMetadata(BaseModel):
    video_id: str
    youtube_url: str
    video_info: Dict
    range_percent: str
    range_seconds: Dict
    total_clips: int
    clips: List[ClipInfo]
    processed_at: str

class ProgressUpdate(BaseModel):
    status: str
    progress: int
    message: str = ""
    timestamp: str