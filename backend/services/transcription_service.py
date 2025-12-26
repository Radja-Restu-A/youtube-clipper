import whisper
import torch
from pathlib import Path

class TranscriptionService:
    def __init__(self, model_name: str, device: str):
        from config import logger
        
        self.model_name = model_name
        self.device = device
        
        logger.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name, device=device)
        logger.info("Model loaded successfully")
    
    def transcribe(self, audio_path: Path, language: str = "id") -> dict:
        """Transcribe audio file"""
        return self.model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            verbose=True,
            fp16=torch.cuda.is_available()
        )