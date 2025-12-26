from pydantic import BaseModel
from typing import Optional, List, Dict

class YouTubeRequest(BaseModel):
    youtube_url: str
    clip_duration: Optional[int] = 45
    range_percent: Optional[str] = "0-100"
    generate_mode: Optional[str] = "audio"  # "audio" | "context" | "viral"  # 🆕 NEW

class ClipInfo(BaseModel):
    clip_id: str
    clip_number: int
    start_time: float
    end_time: float
    duration: int
    engagement_score: float
    output_file: str
    word_count: int
    context_reason: Optional[str] = None
    # 🆕 NEW: Viral-specific fields
    viral_category: Optional[str] = None
    hook_text: Optional[str] = None
    suggested_caption: Optional[str] = None
    loop_hint: Optional[str] = None

class VideoMetadata(BaseModel):
    video_id: str
    youtube_url: str
    video_info: Dict
    range_percent: str
    range_seconds: Dict
    generate_mode: str
    total_clips: int
    clips: List[ClipInfo]
    processed_at: str

class ProgressUpdate(BaseModel):
    status: str
    progress: int
    message: str = ""
    timestamp: str

# 🆕 NEW: Gemini analysis result schema
class ViralClipAnalysis(BaseModel):
    rank: int
    start_time: float
    end_time: float
    duration: float
    hook_text: str
    reason: str
    viral_score: float
    category: str
    suggested_caption: str
    loop_hint: str

class ViralAnalysisResult(BaseModel):
    top_clips: List[ViralClipAnalysis]