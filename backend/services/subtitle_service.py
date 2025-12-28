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
Style: Default,Mogra,80,&H00FFFFFF,&H000000FF,&H004A21ED,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    @staticmethod
    def create_ass_subtitle(words: List[dict], ass_path: Path):
        """Create ASS subtitle with outline - 1 word at a time"""
        from config import logger
        
        ass_content = SubtitleService.ASS_HEADER
        
        # Display 1 word at a time with outline
        for word in words:
            word_text = word['word'].strip().upper()
            start_time = format_ass_time(word['start'])
            end_time = format_ass_time(word['end'])
            
            # Text with outline (white text with pink outline)
            text_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{word_text}\n"
            
            ass_content += text_line
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        logger.info(f"ASS subtitle created with outline: {ass_path}")
    
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