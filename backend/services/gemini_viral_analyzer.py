import google.generativeai as genai
import json
import time
from typing import Dict, List, Optional

class GeminiViralAnalyzer:
    """
    Google Gemini-powered viral segment analyzer for TikTok/Reels/Shorts
    
    CRITICAL: Finds HOOKS (first 3 seconds) then extends to full 30-60s clips
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
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
        clip_duration: int = 45,
        max_retries: int = 3,
        timeout: int = 45
    ) -> Dict:
        """
        Analyze transcript and find top 5 viral-worthy segments
        
        LOGIC:
        1. Gemini identifies HOOK moments (powerful 3-second openers)
        2. Extend each hook to full clip (30-60 seconds of natural conversation)
        3. Score the entire clip (hook quality + content value)
        """
        self.logger.info(f"🔍 Analyzing viral segments for {youtube_url}")
        self.logger.info(f"   Duration: {video_duration}s | Segments: {len(transcript)} | Target clip: {clip_duration}s")
        
        if not transcript or len(transcript) == 0:
            raise ValueError("Empty transcript provided")
        
        # Build prompt with correct logic
        prompt = self._build_viral_analysis_prompt(
            youtube_url, video_duration, transcript, language, clip_duration
        )
        
        # Call Gemini with retry
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"📡 Calling Gemini API (attempt {attempt}/{max_retries})...")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.85,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=4096,
                    ),
                    request_options={"timeout": timeout}
                )
                
                result = self._parse_and_validate_response(
                    response, transcript, video_duration, clip_duration
                )
                
                self.logger.info(f"✅ Gemini analysis complete! {len(result['top_clips'])} clips")
                
                # Log details
                for i, clip in enumerate(result['top_clips']):
                    hook_duration = 3  # First 3 seconds
                    content_duration = clip['duration'] - hook_duration
                    self.logger.info(
                        f"  🔥 Clip {i+1}: {clip['start_time']:.1f}s-{clip['end_time']:.1f}s "
                        f"(Hook: {hook_duration}s + Content: {content_duration:.0f}s) | "
                        f"Score: {clip['viral_score']:.1f} | {clip['category']}"
                    )
                    self.logger.info(f"     Hook: \"{clip['hook_text'][:60]}...\"")
                
                return result
                
            except Exception as e:
                self.logger.error(f"⚠️ Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    self.logger.warning("❌ All retries failed, using fallback")
                    return self._fallback_analysis(transcript, video_duration, clip_duration)
                time.sleep(2 ** attempt)
        
        return self._fallback_analysis(transcript, video_duration, clip_duration)
    
    def _build_viral_analysis_prompt(
        self,
        youtube_url: str,
        video_duration: float,
        transcript: List[Dict],
        language: str,
        clip_duration: int
    ) -> str:
        """Build prompt with CORRECT hook + content logic"""
        
        # Format transcript
        transcript_lines = []
        for seg in transcript:
            ts = f"[{seg['start']:.1f}s → {seg['end']:.1f}s]"
            text = seg.get('text', '').strip()
            if text:
                transcript_lines.append(f"{ts} {text}")
        
        transcript_text = "\n".join(transcript_lines)
        lang_context = "Indonesian podcast (may have English)" if language == "id" else "English"
        
        prompt = f"""You are an expert TikTok/Reels/Shorts content strategist analyzing podcast clips.

VIDEO INFO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL: {youtube_url}
Duration: {video_duration:.1f}s
Language: {lang_context}
Target Clip Length: {clip_duration} seconds
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FULL TRANSCRIPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{transcript_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 YOUR TASK:
Find the TOP 5 viral-worthy HOOK MOMENTS in this podcast, then extend each to a full clip.

⚠️ CRITICAL UNDERSTANDING - CLIP STRUCTURE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each clip has TWO parts:

1. THE HOOK (First 3 seconds)
   ├─ The attention-grabbing opening statement
   ├─ Must create curiosity/shock/interest INSTANTLY
   └─ Examples:
       • "Jadi rahasia yang gak pernah gue kasih tau adalah..."
       • "Ini kesalahan terbesar yang orang lakukan..."
       • "Gue bakal jujur, most people are wrong about..."

2. THE CONTENT (Remaining 27-57 seconds)
   ├─ Natural conversation that FOLLOWS the hook
   ├─ Can be explanation, story, debate, insights
   ├─ Doesn't need to be "perfect" - natural podcast flow is good
   └─ Just needs to maintain interest after the hook

TOTAL CLIP = HOOK (3s) + CONTENT (27-57s) = 30-60 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SELECTION CRITERIA:

1. **HOOK QUALITY** (40% weight)
   - First 3 seconds must GRAB attention
   - Creates immediate curiosity
   - Shocking/controversial/intriguing statement
   - NOT generic like "jadi gini..." or "oke guys..."

2. **CONTENT VALUE** (25% weight)
   - The 30-60s following the hook delivers value
   - Can be: story, insight, explanation, debate, humor
   - Keeps viewer engaged after the hook

3. **EMOTIONAL PEAK** (20% weight)
   - Has emotional high point (surprise, laugh, inspiration)
   - Passionate delivery or strong opinion
   - Relatable or touching moment

4. **VIRALITY POTENTIAL** (15% weight)
   - Will people comment/share?
   - Controversial or thought-provoking?
   - Quotable or meme-worthy?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT TO AVOID:
❌ Long intros without hook ("oke jadi hari ini kita bahas...")
❌ Filler segments with low information density
❌ Subscribe CTAs or outros
❌ Pure silence or background noise
❌ Incomplete thoughts that need prior context

TECHNICAL REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Find 5 DIFFERENT hook moments
✅ Each clip is 30-60 seconds total (hook + content)
✅ Use EXACT timestamps from transcript
✅ NO overlapping clips
✅ Each clip must have UNIQUE content/hook/theme

SCORING (0-100):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
95-100: PERFECT hook + amazing content + highly viral
85-94:  STRONG hook + good content + high viral potential
70-84:  GOOD hook + decent content + moderate viral potential
50-69:  OKAY hook + acceptable content
<50:    DON'T SELECT (weak hook or poor content)

OUTPUT FORMAT (STRICT JSON ONLY):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
  "top_clips": [
    {{
      "rank": 1,
      "start_time": <timestamp where HOOK starts>,
      "end_time": <start_time + 30 to 60 seconds>,
      "duration": <end_time - start_time>,
      "hook_text": "<EXACT text of the hook (first 3 seconds)>",
      "content_summary": "<brief summary of the full 30-60s clip content>",
      "reason": "<why this HOOK+CONTENT combo is viral-worthy>",
      "viral_score": <70-100>,
      "category": "hook|emotional|value|controversial|storytelling",
      "suggested_caption": "<catchy caption for this specific clip>",
      "loop_hint": "<how to loop, or 'N/A'>"
    }}
  ]
}}

EXAMPLE (structure reference):
{{
  "top_clips": [
    {{
      "rank": 1,
      "start_time": 145.2,
      "end_time": 190.5,
      "duration": 45.3,
      "hook_text": "Jadi rahasia yang gak pernah gue kasih tau adalah... investasi terbesar gue bukan di saham",
      "content_summary": "After the hook, explains how he invested in skills instead of stocks, shares 3 specific examples, and reveals the ROI was 10x better",
      "reason": "Powerful curiosity hook about a 'secret', then delivers valuable contrarian advice with specific examples. Will spark debate in comments about investment strategies",
      "viral_score": 94.0,
      "category": "controversial",
      "suggested_caption": "Investasi terbesar gue ternyata bukan saham 😱💰 Ini yang gak pernah gue kasih tau... #InvestasiTips #KontenViral",
      "loop_hint": "Ends with question that loops back to the secret"
    }},
    {{
      "rank": 2,
      "start_time": 312.8,
      "end_time": 355.4,
      "duration": 42.6,
      "hook_text": "Ini momen paling embarrassing dalam hidup gue, literally nangis di depan 500 orang",
      "content_summary": "Tells story of bombing on stage, the humiliation, then the lesson learned about resilience and embracing failure",
      "reason": "Emotional hook about vulnerability, followed by relatable story with clear lesson. High engagement from people sharing their own embarrassing moments",
      "viral_score": 89.5,
      "category": "emotional",
      "suggested_caption": "Momen paling memalukan yang ngajarin gue lesson penting 😭💪 #StoryTime #MotivationMonday",
      "loop_hint": "N/A"
    }}
  ]
}}

NOW ANALYZE THE TRANSCRIPT ABOVE.

Find 5 DIFFERENT hook moments, extend each to 30-60 seconds, and score the complete clips.

Return ONLY the JSON (no markdown, no explanations):"""
        
        return prompt
    
    def _parse_and_validate_response(
        self, 
        response, 
        transcript: List[Dict], 
        video_duration: float,
        target_duration: int
    ) -> Dict:
        """Parse and validate Gemini response"""
        
        try:
            response_text = response.text.strip()
        except AttributeError:
            response_text = str(response).strip()
        
        # Clean markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse failed: {e}")
            self.logger.debug(f"Response: {response_text[:500]}...")
            raise
        
        if "top_clips" not in result:
            raise ValueError("Missing 'top_clips' in response")
        
        clips = result["top_clips"]
        
        if not isinstance(clips, list) or len(clips) < 3:
            raise ValueError(f"Need at least 3 clips, got {len(clips)}")
        
        # Validate and fix clips
        valid_clips = []
        seen_hooks = set()
        
        for i, clip in enumerate(clips[:5]):  # Max 5
            try:
                # Required fields
                required = ["rank", "start_time", "end_time", "hook_text", 
                           "reason", "viral_score", "category", "suggested_caption"]
                
                for field in required:
                    if field not in clip:
                        self.logger.warning(f"Clip {i+1} missing '{field}', skipping")
                        continue
                
                # Validate timestamps
                start = float(clip["start_time"])
                end = float(clip["end_time"])
                
                if start < 0 or end > video_duration:
                    self.logger.warning(f"Clip {i+1} out of bounds, skipping")
                    continue
                
                if end <= start:
                    self.logger.warning(f"Clip {i+1} invalid duration, skipping")
                    continue
                
                duration = end - start
                
                # Validate duration (30-60 seconds)
                if duration < 20 or duration > 70:
                    self.logger.warning(f"Clip {i+1} duration {duration:.1f}s out of range 20-70s")
                    # Try to fix by extending/trimming
                    if duration < 20:
                        end = min(start + target_duration, video_duration)
                    elif duration > 70:
                        end = start + 60
                    duration = end - start
                    clip["end_time"] = end
                    clip["duration"] = duration
                
                # Check for duplicate hooks
                hook_key = clip["hook_text"].lower()[:50]
                if hook_key in seen_hooks:
                    self.logger.warning(f"Clip {i+1} has duplicate hook, skipping")
                    continue
                seen_hooks.add(hook_key)
                
                # Validate score
                score = float(clip.get("viral_score", 70))
                clip["viral_score"] = max(50, min(100, score))
                
                # Ensure duration field
                clip["duration"] = duration
                
                # Add content_summary if missing
                if "content_summary" not in clip:
                    clip["content_summary"] = "Valuable podcast discussion"
                
                valid_clips.append(clip)
                
            except Exception as e:
                self.logger.warning(f"Clip {i+1} validation error: {e}")
                continue
        
        if len(valid_clips) < 3:
            raise ValueError(f"Only {len(valid_clips)} valid clips after validation")
        
        # Check overlaps and fix
        self._fix_overlapping_clips(valid_clips)
        
        # Sort by score
        valid_clips.sort(key=lambda x: x["viral_score"], reverse=True)
        
        # Re-rank
        for i, clip in enumerate(valid_clips):
            clip["rank"] = i + 1
        
        result["top_clips"] = valid_clips[:5]
        
        self.logger.info(f"✅ Validated {len(result['top_clips'])} clips")
        
        return result
    
    def _fix_overlapping_clips(self, clips: List[Dict]):
        """Fix overlapping timestamps"""
        sorted_clips = sorted(clips, key=lambda x: x["start_time"])
        
        for i in range(len(sorted_clips) - 1):
            current = sorted_clips[i]
            next_clip = sorted_clips[i + 1]
            
            if current["end_time"] > next_clip["start_time"]:
                # Fix: trim current clip
                overlap = current["end_time"] - next_clip["start_time"]
                self.logger.warning(f"Overlap {overlap:.1f}s detected, fixing...")
                
                current["end_time"] = next_clip["start_time"] - 1
                current["duration"] = current["end_time"] - current["start_time"]
    
    def _fallback_analysis(
        self, 
        transcript: List[Dict], 
        video_duration: float,
        clip_duration: int
    ) -> Dict:
        """Fallback: find content-rich segments and extend to full clips"""
        self.logger.warning("⚠️ Using fallback analysis")
        
        # Score segments by content richness
        scored_segments = []
        
        for seg in transcript:
            text = seg.get('text', '').strip()
            words = text.split()
            
            if len(words) < 5:
                continue
            
            # Score based on keywords and length
            score = len(words) * 2
            
            keywords = ['jadi', 'sebenarnya', 'rahasia', 'penting', 'intinya',
                       'tips', 'cara', 'harus', 'jangan', 'kesalahan', 'terbaik']
            
            for kw in keywords:
                if kw in text.lower():
                    score += 15
            
            scored_segments.append({
                'start': seg['start'],
                'text': text,
                'score': score
            })
        
        # Sort and take top 5
        scored_segments.sort(key=lambda x: x['score'], reverse=True)
        
        clips = []
        used_ranges = []
        
        for i, seg in enumerate(scored_segments):
            if len(clips) >= 5:
                break
            
            start = seg['start']
            end = min(start + clip_duration, video_duration)
            
            # Check overlap
            overlap = any(
                not (end <= used[0] or start >= used[1])
                for used in used_ranges
            )
            
            if overlap:
                continue
            
            clips.append({
                "rank": i + 1,
                "start_time": start,
                "end_time": end,
                "duration": end - start,
                "hook_text": seg['text'][:100],
                "content_summary": f"Clip segment with {len(seg['text'].split())} words of content",
                "reason": f"Selected by fallback analyzer (score: {seg['score']})",
                "viral_score": 70.0 - (i * 3),
                "category": "value",
                "suggested_caption": f"Insights dari podcast ini 💡 #{i+1}",
                "loop_hint": "N/A"
            })
            
            used_ranges.append((start, end))
        
        return {"top_clips": clips}
    
    def format_for_clipper(self, gemini_result: Dict) -> List[Dict]:
        """Convert Gemini output to clipper format"""
        clips = []
        
        for clip_data in gemini_result["top_clips"]:
            clips.append({
                'clip_id': clip_data['rank'],
                'start': clip_data['start_time'],
                'end': clip_data['end_time'],
                'duration': int(clip_data['duration']),
                'engagement_score': clip_data['viral_score'] / 100,
                'viral_category': clip_data['category'],
                'hook_text': clip_data['hook_text'],
                'content_summary': clip_data.get('content_summary', ''),
                'suggested_caption': clip_data['suggested_caption'],
                'reason': clip_data['reason'],
                'loop_hint': clip_data.get('loop_hint', 'N/A')
            })
        
        return clips