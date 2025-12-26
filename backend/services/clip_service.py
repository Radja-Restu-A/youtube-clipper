from typing import List

class ClipDetectionService:
    @staticmethod
    def find_top_clips(engagement_windows: List[dict], clip_duration: int, 
                      top_n: int = 5) -> List[dict]:
        """Find top N clips based on engagement scores (AUDIO MODE)"""
        from config import logger
        
        logger.info(f"[AUDIO MODE] Finding top {top_n} clips of {clip_duration}s duration")
        
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
    
    @staticmethod
    def find_top_clips_by_context(analyzed_segments: List[dict], 
                                   top_n: int = 5) -> List[dict]:
        """
        Find top N clips based on context scores (CONTEXT MODE)
        
        🆕 NEW METHOD for semantic/conversational analysis
        """
        from config import logger
        
        logger.info(f"[CONTEXT MODE] Selecting top {top_n} clips by semantic value")
        
        # Already sorted by context_score in context_analysis_service
        selected_clips = []
        used_ranges = []
        
        for segment in analyzed_segments:
            if len(selected_clips) >= top_n:
                break
            
            clip_start = segment['start']
            clip_end = segment['end']
            
            # Check overlap with already selected clips
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
                    'duration': int(clip_end - clip_start),
                    'engagement_score': segment['context_score'],
                    'context_reason': segment.get('reason', 'Valuable segment'),
                    'text_preview': segment['text'][:100] + '...' if len(segment['text']) > 100 else segment['text']
                })
                used_ranges.append((clip_start, clip_end))
        
        # Sort by start time for chronological output
        selected_clips.sort(key=lambda x: x['start'])
        
        logger.info(f"[CONTEXT MODE] Selected {len(selected_clips)} clips")
        for i, clip in enumerate(selected_clips):
            logger.info(f"  Clip {i+1}: {clip['start']:.1f}s-{clip['end']:.1f}s | "
                       f"Score: {clip['engagement_score']:.3f} | "
                       f"Reason: {clip['context_reason']}")
        
        return selected_clips