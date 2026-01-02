from pathlib import Path
from dotenv import load_dotenv
import torch
import logging
import os

#initiate environment variables
load_dotenv()

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
TOP_CLIPS_COUNT = 5  # Default (can be overridden by user)
MIN_CLIPS_COUNT = 1  # 🆕 NEW
MAX_CLIPS_COUNT = 20  # 🆕 NEW
MODEL_NAME = "small"

# Context Analysis Settings
CONTEXT_CLIP_MIN_DURATION = 30
CONTEXT_CLIP_MAX_DURATION = 60
CONTEXT_DURATION_FLEX = 15

# 🆕 NEW: Gemini Viral Analyzer Settings

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Set in environment
GEMINI_MODEL = "gemini-1.5-flash"  # Fast and cost-effective
GEMINI_TIMEOUT = 30  # seconds
GEMINI_MAX_RETRIES = 3

# Device detection
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def init_directories():
    """Initialize all required directories"""
    for dir_path in [AUDIO_DIR, CLIPS_DIR, SUBTITLES_DIR, OUTPUT_DIR, HISTORY_DIR, TEMP_DIR]:
        dir_path.mkdir(exist_ok=True)