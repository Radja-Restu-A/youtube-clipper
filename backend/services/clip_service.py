from typing import List

class ClipDetectionService:
    @staticmethod
    def find_top_clips(engagement_windows: List[dict], clip_duration: int, 
                      top_n: int = 5) -> List[dict]:
        """Find top N clips based on engagement scores"""
        from config import logger
        
        logger.info(f"Finding top {top_n} clips of {clip_duration}s duration")
        
        sorted_windows = sorted(engagement_windows, 
                              key=lambda x: x['engagement_score'], 
                              reverse=True)
        
        selected_clips = []
        used_ranges = []
        
        for window in sorted_windows:
            if len(selected_clips) >= top_n:
                break
            
            clip_start = window['start']
            clip_end = clip_start + clip_duration
            
            # Check overlap
            overlap = False
            for used_start, used_end in used_ranges:
                if not (clip_end <= used_start or clip_start >= used_end):
                    overlap = True
                    break
            
            if not overlap:
                selected_clips.append({
                    'clip_id': len(selected_clips) + 1,
                    'start': clip_start,
                    'end': clip_end,
                    'duration': clip_duration,
                    'engagement_score': window['engagement_score']
                })
                used_ranges.append((clip_start, clip_end))
        
        selected_clips.sort(key=lambda x: x['start'])
        
        logger.info(f"Selected {len(selected_clips)} clips")
        return selected_clips