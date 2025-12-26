from typing import List, Dict
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class LLMService:
    """Local semantic analysis using IndoBERT"""
    
    def __init__(self):
        from config import logger
        
        self.logger = logger
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Use IndoBERT for Indonesian language understanding
        model_name = "indobenchmark/indobert-base-p1"
        
        try:
            self.logger.info(f"Loading IndoBERT model on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.model.eval()
            self.logger.info("IndoBERT model loaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to load IndoBERT: {e}. Using fallback scoring.")
            self.model = None
            self.tokenizer = None
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get sentence embedding using IndoBERT"""
        if self.model is None:
            return np.random.rand(768)  # Fallback
        
        try:
            inputs = self.tokenizer(text, return_tensors="pt", 
                                   truncation=True, max_length=512,
                                   padding=True).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use [CLS] token embedding
                embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            return embedding[0]
        except Exception as e:
            self.logger.error(f"Embedding error: {e}")
            return np.random.rand(768)
    
    def analyze_segments(self, segments: List[Dict], full_text: str) -> List[Dict]:
        """Analyze segments for semantic importance"""
        self.logger.info(f"Analyzing {len(segments)} segments for context...")
        
        analyzed = []
        
        # Get embedding for full context
        context_embedding = self.get_embedding(full_text[:2000])  # First 2000 chars as context
        
        for segment in segments:
            text = segment['text'].strip()
            
            if len(text) < 10:  # Skip very short segments
                continue
            
            # Get segment embedding
            segment_embedding = self.get_embedding(text)
            
            # Calculate semantic features
            context_similarity = float(cosine_similarity(
                [segment_embedding], 
                [context_embedding]
            )[0][0])
            
            # Rule-based scoring
            semantic_score = self._calculate_semantic_score(text)
            conversational_score = self._detect_conversational_signals(text)
            density_score = self._calculate_information_density(text)
            standalone_score = self._assess_standalone_quality(text)
            
            # Combined context score
            context_score = (
                semantic_score * 0.40 +
                conversational_score * 0.25 +
                density_score * 0.20 +
                standalone_score * 0.15
            )
            
            analyzed.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': text,
                'context_score': float(context_score),
                'context_similarity': context_similarity,
                'semantic_score': semantic_score,
                'conversational_score': conversational_score,
                'reason': self._generate_reason(text, context_score)
            })
        
        self.logger.info(f"Analyzed {len(analyzed)} valid segments")
        return analyzed
    
    def _calculate_semantic_score(self, text: str) -> float:
        """Calculate semantic importance score"""
        text_lower = text.lower()
        
        # Keywords indicating important content
        importance_keywords = [
            'penting', 'intinya', 'kesimpulan', 'jadi', 'sebenarnya',
            'point', 'key', 'basically', 'fundamental', 'essential',
            'harus', 'wajib', 'perlu', 'sebaiknya', 'disarankan',
            'rahasia', 'tips', 'cara', 'strategi', 'solusi',
            'masalah', 'tantangan', 'issue', 'problem',
            'insight', 'pembelajaran', 'pengalaman', 'cerita',
            'fakta', 'data', 'riset', 'research', 'studi'
        ]
        
        score = 0.0
        for keyword in importance_keywords:
            if keyword in text_lower:
                score += 0.05
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _detect_conversational_signals(self, text: str) -> float:
        """Detect conversational turning points"""
        text_lower = text.lower()
        
        # Strong conversational signals
        strong_signals = [
            'jadi intinya', 'yang penting adalah', 'kesimpulannya',
            'pelajaran terbesar', 'hal yang paling', 'kunci utama',
            'satu hal yang', 'jujur aja', 'menurut gue', 'menurut saya',
            'percaya deh', 'trust me', 'believe me', 'honestly',
            'tapi masalahnya', 'nah ini dia', 'nah makanya',
            'kalau menurut', 'pengalaman gue', 'pengalaman saya',
            'ternyata', 'akhirnya', 'finally', 'eventually'
        ]
        
        score = 0.0
        for signal in strong_signals:
            if signal in text_lower:
                score += 0.15
        
        # Emotional markers
        emotional_markers = ['banget', 'sangat', 'sekali', 'really', 'very', 
                            'incredible', 'amazing', 'wow', 'gila']
        for marker in emotional_markers:
            if marker in text_lower:
                score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_information_density(self, text: str) -> float:
        """Calculate information density (meaningful words ratio)"""
        words = text.lower().split()
        
        if len(words) == 0:
            return 0.0
        
        # Filler words/phrases in Indonesian & English
        fillers = {
            'ya', 'iya', 'oh', 'eh', 'um', 'uh', 'hmm', 'emm',
            'gitu', 'sih', 'kan', 'deh', 'dong', 'kok',
            'like', 'you know', 'i mean', 'sort of', 'kind of',
            'actually', 'basically', 'literally',
            'terus', 'trus', 'nah', 'lah', 'nih'
        }
        
        filler_count = sum(1 for word in words if word in fillers)
        meaningful_ratio = 1.0 - (filler_count / len(words))
        
        # Length bonus (longer segments tend to have more info)
        length_bonus = min(len(words) / 100, 0.3)
        
        return min(meaningful_ratio + length_bonus, 1.0)
    
    def _assess_standalone_quality(self, text: str) -> float:
        """Assess if segment can stand alone"""
        score = 0.5  # Base score
        
        # Complete sentences (has ending punctuation)
        if text.strip().endswith(('.', '!', '?')):
            score += 0.2
        
        # Not too many pronouns (dia, itu, ini, that, this)
        pronouns = ['dia', 'itu', 'ini', 'itu', 'that', 'this', 'those', 'these']
        words = text.lower().split()
        if len(words) > 0:
            pronoun_ratio = sum(1 for w in words if w in pronouns) / len(words)
            score -= pronoun_ratio * 0.3
        
        # Has concrete nouns/concepts
        if any(len(word) > 6 for word in words):  # Longer words tend to be concrete
            score += 0.2
        
        return max(0.0, min(score, 1.0))
    
    def _generate_reason(self, text: str, score: float) -> str:
        """Generate human-readable reason for selection"""
        text_lower = text.lower()
        
        if score > 0.8:
            if any(k in text_lower for k in ['intinya', 'kesimpulan', 'penting']):
                return "Key insight or conclusion"
            elif any(k in text_lower for k in ['pengalaman', 'cerita', 'story']):
                return "Valuable experience/story"
            else:
                return "High semantic value"
        elif score > 0.6:
            if any(k in text_lower for k in ['jadi', 'sebenarnya', 'basically']):
                return "Clear explanation or turning point"
            else:
                return "Meaningful discussion point"
        else:
            return "Informative segment"