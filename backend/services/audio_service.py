import librosa
import numpy as np
from typing import List
from pathlib import Path

class AudioAnalysisService:
    @staticmethod
    def analyze_engagement(audio_path: Path) -> List[dict]:
        """Analyze audio to find most engaging segments"""
        from config import logger
        
        logger.info(f"Analyzing audio engagement: {audio_path}")
        
        try:
            y, sr = librosa.load(str(audio_path), sr=22050)
            duration = librosa.get_duration(y=y, sr=sr)
            
            window_size = 5  # seconds
            hop_size = 1  # seconds
            
            windows = []
            for start in np.arange(0, duration - window_size, hop_size):
                end = start + window_size
                start_sample = int(start * sr)
                end_sample = int(end * sr)
                
                window_audio = y[start_sample:end_sample]
                
                # Calculate features
                rms = np.sqrt(np.mean(window_audio**2))
                zcr = np.mean(librosa.zero_crossings(window_audio))
                spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=window_audio, sr=sr))
                onset_env = librosa.onset.onset_strength(y=window_audio, sr=sr)
                tempo_strength = np.mean(onset_env)
                
                # Combined engagement score
                engagement_score = (
                    rms * 0.4 +
                    zcr * 0.2 +
                    (spectral_centroid / 5000) * 0.2 +
                    tempo_strength * 0.2
                )
                
                windows.append({
                    'start': start,
                    'end': end,
                    'engagement_score': float(engagement_score),
                    'rms': float(rms),
                    'zcr': float(zcr)
                })
            
            logger.info(f"Analyzed {len(windows)} windows")
            return windows
            
        except Exception as e:
            logger.error(f"Error analyzing audio: {str(e)}")
            raise Exception(f"Failed to analyze audio: {str(e)}")
