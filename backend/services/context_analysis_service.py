from typing import List, Dict
from pathlib import Path
from .llm_service import LLMService

class ContextAnalysisService:
    """Context-based clip analysis using semantic understanding"""
    
    def __init__(self):
        from config import logger
        self.logger = logger
        self.llm = LLMService()
    
    def analyze_transcript_for_clips(self, transcription_result: dict, 
                                     clip_duration: int = 45,
                                     duration_flex: int = 15) -> List[Dict]:
        """
        Analyze transcript and find semantically important segments
        
        Args:
            transcription_result: Whisper transcription output
            clip_duration: Target clip duration in seconds
            duration_flex: Flexibility in duration (±seconds)
        
        Returns:
            List of analyzed segments with context scores
        """
        self.logger.info("Starting context-based transcript analysis...")
        
        # Extract segments from transcription
        segments = transcription_result.get('segments', [])
        full_text = transcription_result.get('text', '')
        
        if not segments:
            raise ValueError("No segments found in transcription")
        
        # Group segments into potential clips (target duration ± flex)
        min_duration = clip_duration - duration_flex
        max_duration = clip_duration + duration_flex
        
        candidate_clips = self._create_candidate_clips(
            segments, min_duration, max_duration, clip_duration
        )
        
        self.logger.info(f"Created {len(candidate_clips)} candidate clips")
        
        # Analyze each candidate with LLM
        analyzed_clips = self.llm.analyze_segments(candidate_clips, full_text)
        
        # Sort by context score
        analyzed_clips.sort(key=lambda x: x['context_score'], reverse=True)
        
        return analyzed_clips
    
    def _create_candidate_clips(self, segments: List[Dict], 
                                min_dur: int, max_dur: int, 
                                target_dur: int) -> List[Dict]:
        """
        Create candidate clips by grouping consecutive segments
        """
        candidates = []
        
        i = 0
        while i < len(segments):
            start_segment = segments[i]
            start_time = start_segment['start']
            current_duration = 0
            combined_text = []
            
            j = i
            while j < len(segments):
                segment = segments[j]
                segment_duration = segment['end'] - start_time
                
                # Check if adding this segment keeps us in range
                if segment_duration <= max_dur:
                    combined_text.append(segment['text'])
                    current_duration = segment_duration
                    j += 1
                else:
                    break
            
            # Only add if duration is reasonable
            if min_dur <= current_duration <= max_dur:
                candidates.append({
                    'start': start_time,
                    'end': start_time + current_duration,
                    'duration': current_duration,
                    'text': ' '.join(combined_text),
                    'segment_count': j - i
                })
            
            # Move window forward (slide by 1 segment for overlap)
            i += max(1, (j - i) // 2)  # Slide by half the window
        
        return candidates
    
    def expand_clip_to_natural_boundary(self, segments: List[Dict], 
                                       start: float, end: float,
                                       max_expand: int = 10) -> tuple:
        """
        Expand clip boundaries to natural sentence breaks
        """
        # Find segments that overlap with current clip
        clip_segments = [s for s in segments 
                        if s['start'] >= start - max_expand 
                        and s['end'] <= end + max_expand]
        
        if not clip_segments:
            return start, end
        
        # Find natural boundaries (segments ending with punctuation)
        new_start = start
        new_end = end
        
        # Expand start backward to sentence start
        for seg in reversed(clip_segments):
            if seg['end'] <= start:
                text = seg['text'].strip()
                if text and text[0].isupper():  # Starts with capital
                    new_start = seg['start']
                    break
        
        # Expand end forward to sentence end
        for seg in clip_segments:
            if seg['start'] >= end:
                text = seg['text'].strip()
                if text and text[-1] in '.!?':  # Ends with punctuation
                    new_end = seg['end']
                    break
        
        return new_start, new_end