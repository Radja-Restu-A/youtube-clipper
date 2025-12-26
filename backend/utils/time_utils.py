def parse_range_percent(range_str: str, total_duration: float) -> tuple:
    """Parse range percentage string and convert to seconds"""
    try:
        start_percent, end_percent = map(int, range_str.split('-'))
        
        if not (0 <= start_percent < end_percent <= 100):
            raise ValueError("Invalid range: start must be < end, both in 0-100")
        
        start_seconds = (start_percent / 100) * total_duration
        end_seconds = (end_percent / 100) * total_duration
        
        return start_seconds, end_seconds
        
    except Exception as e:
        raise ValueError(f"Invalid range format. Use format like '0-25', '26-50', etc.")

def format_ass_time(seconds: float) -> str:
    """Format seconds to ASS time format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"