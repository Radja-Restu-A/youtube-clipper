import re
from pathlib import Path
from typing import List

def clean_subtitle_text(text: str) -> str:
    """Remove unwanted punctuation from subtitle text"""
    text = re.sub(r"[-\.,]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def cleanup_temp_files(video_id: str, patterns: List[Path]):
    """Clean up temporary files"""
    from config import logger
    
    logger.info(f"Cleaning up temporary files for {video_id}")
    
    for pattern in patterns:
        for file in pattern.parent.glob(pattern.name):
            try:
                file.unlink()
                logger.info(f"Deleted: {file}")
            except Exception as e:
                logger.warning(f"Could not delete {file}: {e}")
