import google.generativeai as genai
import json
import time
from typing import Dict, List, Optional
from pathlib import Path

class GeminiViralAnalyzer:
    """
    Google Gemini-powered viral segment analyzer for TikTok/Reels/Shorts
    
    Analyzes transcripts to find top 5 viral-worthy segments based on:
    - Hook quality (first 3 seconds)
    - High-emotion moments
    - Value bombs (instant education/motivation)
    - Controversial/strong opinions
    - Loopability
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Initialize Gemini analyzer
        
        Args:
            api_key: Google Gemini API key
            model_name: Model to use (default: gemini-1.5-flash for speed)
        """
        from config import logger
        
        self.logger = logger
        self.model_name = model_name
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.logger.info(f"✅ Gemini Viral Analyzer initialized with {model_name}")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Gemini: {e}")
            raise
    
    def analyze_viral_segments(
        self,
        youtube_url: str,
        video_duration: float,
        transcript: List[Dict],
        language: str = "id",
        max_retries: int = 3,
        timeout: int = 30
    ) -> Dict:
        """
        Analyze transcript and find top 5 viral-worthy segments
        
        Args:
            youtube_url: YouTube video URL
            video_duration: Total video duration in seconds
            transcript: Whisper transcript segments
            language: Video language (id/en)
            max_retries: Max retry attempts
            timeout: Request timeout in seconds
        
        Returns:
            Structured viral analysis result
        """
        self.logger.info(f"🔍 Analyzing viral segments for {youtube_url}")
        self.logger.info(f"   Duration: {video_duration}s | Segments: {len(transcript)} | Language: {language}")
        
        # Build prompt
        prompt = self._build_viral_analysis_prompt(
            youtube_url, video_duration, transcript, language
        )
        
        # Call Gemini with retry logic
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"📡 Calling Gemini API (attempt {attempt}/{max_retries})...")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=2048,
                    ),
                    request_options={"timeout": timeout}
                )
                
                # Extract and validate response
                result = self._parse_and_validate_response(response)
                
                self.logger.info(f"✅ Gemini analysis complete! Found {len(result['top_clips'])} viral segments")
                return result
                
            except json.JSONDecodeError as e:
                self.logger.error(f"⚠️ JSON parse error (attempt {attempt}): {e}")
                if attempt == max_retries:
                    return self._fallback_analysis(transcript, video_duration)
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                self.logger.error(f"⚠️ Gemini API error (attempt {attempt}): {e}")
                if attempt == max_retries:
                    return self._fallback_analysis(transcript, video_duration)
                time.sleep(2 ** attempt)
        
        # Should never reach here, but just in case
        return self._fallback_analysis(transcript, video_duration)
    
    def _build_viral_analysis_prompt(
        self,
        youtube_url: str,
        video_duration: float,
        transcript: List[Dict],
        language: str
    ) -> str:
        """Build the Gemini prompt for viral analysis"""
        
        # Prepare transcript text
        transcript_text = self._format_transcript_for_prompt(transcript)
        
        lang_context = "Indonesian (with occasional English code-switching)" if language == "id" else "English"
        
        prompt = f"""You are an expert TikTok/Reels/Shorts content analyzer. Your task is to identify the TOP 5 most viral-worthy segments from this video transcript.

VIDEO METADATA:
- URL: {youtube_url}
- Duration: {video_duration} seconds
- Language: {lang_context}

TRANSCRIPT:
{transcript_text}

ANALYSIS CRITERIA (MANDATORY):
1. **The Hook (First 3 seconds)**: Opening that immediately grabs attention or sparks curiosity
2. **High-Emotion Moments**: Shocking statements, contagious laughter, touching moments
3. **Value Bombs**: Quick insights that deliver instant education or motivation
4. **Controversial/Strong Opinions**: Statements likely to trigger comments and debate
5. **Loopability**: Segments where the ending can smoothly connect back to the beginning

REQUIREMENTS:
✅ Select EXACTLY 5 segments
✅ Each segment must be 15-60 seconds (ideal: 30-45 seconds)
✅ NO overlapping timestamps
✅ AVOID: Long intros, filler words, subscribe CTAs, dead air
✅ Prioritize segments with clear hooks and strong emotional peaks
✅ Consider Indonesian viral trends (relatable stories, controversial takes, life lessons)

OUTPUT FORMAT (CRITICAL):
Return ONLY valid JSON, no markdown, no explanations, no extra text.

{{
  "top_clips": [
    {{
      "rank": 1,
      "start_time": <float>,
      "end_time": <float>,
      "duration": <float>,
      "hook_text": "<first impactful sentence>",
      "reason": "<why this segment will go viral>",
      "viral_score": <0-100>,
      "category": "<hook|emotional|value|controversial|storytelling>",
      "suggested_caption": "<catchy caption for social media>",
      "loop_hint": "<how to loop this clip, or 'N/A'>"
    }}
  ]
}}

SCORING GUIDE:
- 90-100: Extremely viral (instant hook + emotional peak + shareability)
- 70-89: High potential (strong hook + clear value)
- 50-69: Good clip (decent hook + some engagement)
- Below 50: Filler content (avoid selecting)

Order by viral_score descending. Ensure timestamps are accurate and match the transcript.

Now analyze and return ONLY the JSON:"""
        
        return prompt
    
    def _format_transcript_for_prompt(self, transcript: List[Dict]) -> str:
        """Format transcript segments for prompt"""
        lines = []
        for seg in transcript:
            timestamp = f"[{seg['start']:.1f}s - {seg['end']:.1f}s]"
            text = seg.get('text', '').strip()
            if text:
                lines.append(f"{timestamp} {text}")
        
        return "\n".join(lines)
    
    def _parse_and_validate_response(self, response) -> Dict:
        """Parse and validate Gemini response"""
        
        # Extract text from response
        try:
            response_text = response.text.strip()
        except AttributeError:
            response_text = str(response).strip()
        
        self.logger.debug(f"Raw Gemini response: {response_text[:500]}...")
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "", 1)
        if response_text.startswith("```"):
            response_text = response_text.replace("```", "", 1)
        if response_text.endswith("```"):
            response_text = response_text.rsplit("```", 1)[0]
        
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise ValueError("No valid JSON found in response")
        
        # Validate schema
        self._validate_viral_response(result)
        
        return result
    
    def _validate_viral_response(self, result: Dict):
        """Validate response against expected schema"""
        
        if "top_clips" not in result:
            raise ValueError("Missing 'top_clips' in response")
        
        clips = result["top_clips"]
        
        if not isinstance(clips, list):
            raise ValueError("'top_clips' must be a list")
        
        if len(clips) != 5:
            self.logger.warning(f"⚠️ Expected 5 clips, got {len(clips)}")
        
        required_fields = [
            "rank", "start_time", "end_time", "duration",
            "hook_text", "reason", "viral_score", "category",
            "suggested_caption", "loop_hint"
        ]
        
        for i, clip in enumerate(clips):
            for field in required_fields:
                if field not in clip:
                    raise ValueError(f"Clip {i+1} missing required field: {field}")
            
            # Validate types and ranges
            if not isinstance(clip["rank"], int) or not (1 <= clip["rank"] <= 5):
                raise ValueError(f"Invalid rank in clip {i+1}: {clip['rank']}")
            
            if not isinstance(clip["viral_score"], (int, float)) or not (0 <= clip["viral_score"] <= 100):
                raise ValueError(f"Invalid viral_score in clip {i+1}: {clip['viral_score']}")
            
            if not isinstance(clip["start_time"], (int, float)) or clip["start_time"] < 0:
                raise ValueError(f"Invalid start_time in clip {i+1}: {clip['start_time']}")
            
            if not isinstance(clip["end_time"], (int, float)) or clip["end_time"] <= clip["start_time"]:
                raise ValueError(f"Invalid end_time in clip {i+1}: {clip['end_time']}")
            
            # Validate category
            valid_categories = ["hook", "emotional", "value", "controversial", "storytelling"]
            if clip["category"] not in valid_categories:
                self.logger.warning(f"⚠️ Unknown category in clip {i+1}: {clip['category']}")
        
        # Check for overlaps
        self._check_clip_overlaps(clips)
        
        self.logger.info("✅ Response validation passed")
    
    def _check_clip_overlaps(self, clips: List[Dict]):
        """Check if clips have overlapping timestamps"""
        sorted_clips = sorted(clips, key=lambda x: x["start_time"])
        
        for i in range(len(sorted_clips) - 1):
            current = sorted_clips[i]
            next_clip = sorted_clips[i + 1]
            
            if current["end_time"] > next_clip["start_time"]:
                self.logger.warning(
                    f"⚠️ Overlap detected: Clip ending at {current['end_time']}s "
                    f"overlaps with clip starting at {next_clip['start_time']}s"
                )
    
    def _fallback_analysis(self, transcript: List[Dict], video_duration: float) -> Dict:
        """
        Fallback analysis when Gemini fails
        Uses simple heuristics to select segments
        """
        self.logger.warning("⚠️ Using fallback viral analysis (Gemini unavailable)")
        
        # Simple heuristic: divide video into 5 equal parts
        segment_duration = min(45, video_duration / 6)  # Max 45s per clip
        clips = []
        
        for i in range(5):
            start = i * (video_duration / 5)
            end = start + segment_duration
            
            if end > video_duration:
                end = video_duration
            
            clips.append({
                "rank": i + 1,
                "start_time": float(start),
                "end_time": float(end),
                "duration": float(end - start),
                "hook_text": "Auto-generated segment",
                "reason": "Selected by fallback analyzer",
                "viral_score": 50.0,
                "category": "value",
                "suggested_caption": "Check this out! 🔥",
                "loop_hint": "N/A"
            })
        
        return {"top_clips": clips}
    
    def format_for_clipper(self, gemini_result: Dict) -> List[Dict]:
        """
        Convert Gemini output to clipper-compatible format
        
        Args:
            gemini_result: Output from analyze_viral_segments()
        
        Returns:
            List of clips in clipper format
        """
        clips = []
        
        for clip_data in gemini_result["top_clips"]:
            clips.append({
                'clip_id': clip_data['rank'],
                'start': clip_data['start_time'],
                'end': clip_data['end_time'],
                'duration': int(clip_data['duration']),
                'engagement_score': clip_data['viral_score'] / 100,  # Normalize to 0-1
                'viral_category': clip_data['category'],
                'hook_text': clip_data['hook_text'],
                'suggested_caption': clip_data['suggested_caption'],
                'reason': clip_data['reason']
            })
        
        return clips