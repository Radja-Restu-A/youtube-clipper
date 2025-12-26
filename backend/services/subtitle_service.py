from typing import List
from pathlib import Path
from utils.time_utils import format_ass_time
from utils.file_utils import clean_subtitle_text

class SubtitleService:
    ASS_HEADER = """[Script Info]
Title: Opus Clip Style Subtitle
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    @staticmethod
    def create_ass_subtitle(words: List[dict], ass_path: Path):
        """Create ASS subtitle with Opus Clip style"""
        from config import logger
        
        ass_content = SubtitleService.ASS_HEADER
        
        # Group words into lines (max 6 words per line)
        lines = []
        current_line = []
        
        for i, word in enumerate(words):
            current_line.append(word)
            if len(current_line) >= 6 or i == len(words) - 1:
                if current_line:
                    lines.append(current_line)
                    current_line = []
        
        # Generate subtitle events
        for line_words in lines:
            if not line_words:
                continue
            
            for word_idx, word in enumerate(line_words):
                text_parts = []
                
                for i, w in enumerate(line_words):
                    word_upper = w['word'].strip().upper()
                    
                    if i == word_idx:
                        text_parts.append(f"{{\\c&H00FF00&\\b1}}{word_upper}{{\\c&HFFFFFF&\\b0}}")
                    else:
                        text_parts.append(word_upper)
                
                full_text = " ".join(text_parts)
                start_time = format_ass_time(word['start'])
                end_time = format_ass_time(word['end'])
                
                ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{full_text}\n"
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        logger.info(f"ASS subtitle created: {ass_path}")
    
    @staticmethod
    def extract_clip_words(result: dict, clip_start: float, clip_end: float) -> List[dict]:
        """Extract words for specific clip time range"""
        clip_words = []
        
        for segment in result["segments"]:
            if "words" in segment:
                for word_info in segment["words"]:
                    word_time = word_info["start"]
                    if clip_start <= word_time <= clip_end:
                        clean_word = clean_subtitle_text(word_info["word"])
                        
                        if not clean_word:
                            continue
                        
                        clip_words.append({
                            "word": clean_word.strip().upper(),
                            "start": round(word_info["start"] - clip_start, 2),
                            "end": round(word_info["end"] - clip_start, 2)
                        })
        
        return clip_words