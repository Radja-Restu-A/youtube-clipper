from pathlib import Path
import torch
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories
BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
CLIPS_DIR = BASE_DIR / "clips"
SUBTITLES_DIR = BASE_DIR / "subtitles"
OUTPUT_DIR = BASE_DIR / "output"
HISTORY_DIR = BASE_DIR / "history"
TEMP_DIR = BASE_DIR / "temp"

# Constants
MAX_DURATION_SECONDS = 7200  # 2 hours
CLIP_DURATION = 45  # seconds per clip
TOP_CLIPS_COUNT = 5
MODEL_NAME = "small"

# 🆕 NEW: Context Analysis Settings
CONTEXT_CLIP_MIN_DURATION = 30  # Minimum clip duration for context mode
CONTEXT_CLIP_MAX_DURATION = 60  # Maximum clip duration for context mode
CONTEXT_DURATION_FLEX = 15      # Flexibility in duration (±seconds)

# Device detection
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def init_directories():
    """Initialize all required directories"""
    for dir_path in [AUDIO_DIR, CLIPS_DIR, SUBTITLES_DIR, OUTPUT_DIR, HISTORY_DIR, TEMP_DIR]:
        dir_path.mkdir(exist_ok=True)