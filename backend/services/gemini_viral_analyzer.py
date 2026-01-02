import google.generativeai as genai
import json
import time
from typing import Dict, List, Optional

class GeminiViralAnalyzer:
    """
    Google Gemini-powered viral segment analyzer
    
    Analyzes video context (title + description) + transcript
    to find most relevant and viral-worthy clips
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
        video_title: str,
        video_description: str,
        video_duration: float,
        transcript: List[Dict],
        language: str = "id",
        clip_duration: int = 45,
        total_clips: int = 5,  # 🆕 Dynamic clip count
        max_retries: int = 3,
        timeout: int = 45
    ) -> Dict:
        """
        Analyze video and find top N viral clips that match video theme
        
        Args:
            youtube_url: YouTube URL
            video_title: Video title (for context)
            video_description: Video description (for context)
            video_duration: Total duration
            transcript: Full transcript
            language: Language code
            clip_duration: Target clip length
            total_clips: Number of clips to generate (1-20)
            max_retries: Retry attempts
            timeout: Request timeout
        
        Returns:
            Dict with top_clips array
        """
        self.logger.info(f"🔍 Analyzing {total_clips} viral segments for: {video_title}")
        self.logger.info(f"   Duration: {video_duration}s | Segments: {len(transcript)} | Target: {clip_duration}s")
        
        if not transcript or len(transcript) == 0:
            raise ValueError("Empty transcript provided")
        
        # Build context-aware prompt
        prompt = self._build_context_aware_prompt(
            youtube_url=youtube_url,
            video_title=video_title,
            video_description=video_description,
            video_duration=video_duration,
            transcript=transcript,
            language=language,
            clip_duration=clip_duration,
            total_clips=total_clips  # 🆕 Pass to prompt
        )
        
        # Call Gemini with retry
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"📡 Calling Gemini API (attempt {attempt}/{max_retries})...")
                
                # 🆕 Adjust timeout and tokens based on clip count
                adjusted_timeout = timeout + (total_clips * 2)
                max_tokens = 4096 + (total_clips * 200)
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.85,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=max_tokens,
                    ),
                    request_options={"timeout": adjusted_timeout}
                )
                
                # 🆕 Pass expected clip count to validation
                result = self._parse_and_validate_response(
                    response, transcript, video_duration, clip_duration, total_clips
                )
                
                actual_count = len(result['top_clips'])
                self.logger.info(f"✅ Analysis complete! {actual_count}/{total_clips} clips generated")
                
                # Log clips with relevance scores
                for i, clip in enumerate(result['top_clips']):
                    self.logger.info(
                        f"  🔥 Clip {i+1}/{actual_count}: {clip['start_time']:.1f}s-{clip['end_time']:.1f}s | "
                        f"Score: {clip['viral_score']:.1f} | "
                        f"Relevance: {clip.get('theme_relevance', 'N/A')[:30]}... | "
                        f"{clip['category']}"
                    )
                
                return result
                
            except Exception as e:
                self.logger.error(f"⚠️ Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    self.logger.warning("❌ All retries failed, using fallback")
                    return self._fallback_analysis(transcript, video_duration, clip_duration, total_clips)
                time.sleep(2 ** attempt)
        
        return self._fallback_analysis(transcript, video_duration, clip_duration, total_clips)
    
    def _build_context_aware_prompt(
        self,
        youtube_url: str,
        video_title: str,
        video_description: str,
        video_duration: float,
        transcript: List[Dict],
        language: str,
        clip_duration: int,
        total_clips: int = 5  # 🆕 Dynamic
    ) -> str:
        """Build context-aware prompt that considers video theme"""
        
        # Format transcript
        transcript_lines = []
        for seg in transcript:
            ts = f"[{seg['start']:.1f}s → {seg['end']:.1f}s]"
            text = seg.get('text', '').strip()
            if text:
                transcript_lines.append(f"{ts} {text}")
        
        transcript_text = "\n".join(transcript_lines)
        lang_context = "Indonesian podcast (may have English code-switching)" if language == "id" else "English"
        
        # Clean description (first 500 chars)
        description_preview = (video_description[:500] + "...") if len(video_description) > 500 else video_description
        
        prompt = f"""You are an expert viral content strategist analyzing a YouTube video.

VIDEO CONTEXT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📺 TITLE: {video_title}

📝 DESCRIPTION:
{description_preview}

🌐 URL: {youtube_url}
⏱️  Duration: {video_duration:.1f} seconds
🗣️  Language: {lang_context}
🎯 Target Clip Length: {clip_duration} seconds
🎬 Clips Requested: {total_clips}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FULL TRANSCRIPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{transcript_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 YOUR MISSION:

⚠️ CRITICAL REQUIREMENT: You MUST return EXACTLY {total_clips} clips in the JSON response!

Analyze this video holistically and find the TOP {total_clips} viral-worthy clips that:

1. ✅ **MATCH THE VIDEO THEME** - Clips must be DIRECTLY RELEVANT to what the title/description promise
2. ✅ **HAVE POWERFUL HOOKS** - First 3 seconds grab attention immediately
3. ✅ **DELIVER VALUE** - The 30-60s clip delivers insights/entertainment related to the theme
4. ✅ **ARE VIRAL-WORTHY** - High engagement, shareable, comment-worthy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP-BY-STEP ANALYSIS PROCESS:

STEP 1: Understand Video Theme
- What is this video primarily about based on title + description?
- What topics/themes are promised to viewers?
- What would viewers expect to learn/see?

STEP 2: Find Theme-Matching Moments
- Scan transcript for segments that DIRECTLY address the main theme
- Look for moments where the speaker delivers on the title's promise
- Prioritize segments that answer "what viewers came for"

STEP 3: Identify Hooks Within Theme-Relevant Segments
- Within theme-relevant parts, find powerful 3-second hooks
- Hook must create curiosity about the theme topic
- Hook should make viewers want to hear more about the theme

STEP 4: Extend to Full Clips
- Extend each hook to 30-60 seconds of natural conversation
- Ensure the full clip delivers valuable content about the theme
- Content should feel complete and satisfying

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLIP SELECTION CRITERIA (WEIGHTED SCORING):

Calculate viral_score using this formula:

viral_score = (
  (theme_relevance_score × 0.30) +      // 30% - Does it deliver on title promise?
  (hook_quality_score × 0.35) +         // 35% - How strong is the 3-second hook?
  (content_value_score × 0.20) +        // 20% - Value of full 30-60s content
  (virality_potential_score × 0.15)     // 15% - Shareability/engagement potential
)

Each component scored 0-100, then apply weights.

1. **THEME RELEVANCE SCORE** (30% weight) 🎯
   100: Perfectly addresses exact topic in title
   85:  Strongly related to main theme
   70:  Clearly connected to theme
   55:  Somewhat related to theme
   40:  Tangentially related
   
2. **HOOK QUALITY SCORE** (35% weight) 🎣
   100: Instant scroll-stopper, creates massive curiosity
   85:  Very strong hook, makes you want to keep watching
   70:  Good hook, sparks interest
   55:  Decent hook, somewhat engaging
   40:  Weak hook
   
3. **CONTENT VALUE SCORE** (20% weight) 💎
   100: Delivers exceptional insights/entertainment
   85:  Strong value, actionable/memorable
   70:  Good content, worth watching
   55:  Acceptable content
   40:  Basic content
   
4. **VIRALITY POTENTIAL SCORE** (15% weight) 🔥
   100: Will definitely spark massive engagement
   85:  High chance of comments/shares
   70:  Likely to get decent engagement
   55:  Some viral elements
   40:  Low viral potential

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT TO AVOID:
❌ Off-topic tangents (even if entertaining)
❌ Generic intros not related to theme
❌ Filler conversations that don't address main topic
❌ CTAs and outros
❌ Segments that don't deliver on title's promise

DIVERSITY WITHIN THEME:
- All {total_clips} clips should relate to the SAME main theme
- But cover DIFFERENT aspects/angles of that theme

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TECHNICAL REQUIREMENTS:
✅ Each clip: 30-60 seconds (hook 3s + content 27-57s)
✅ Use EXACT timestamps from transcript
✅ NO overlapping clips
✅ EXACTLY {total_clips} DIFFERENT segments covering different aspects of theme

SCORING (0-100) - BE GENEROUS BUT FAIR:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⭐ 85-100: EXCEPTIONAL
⭐ 75-84: VERY GOOD (Most viral clips fall here!)
⭐ 65-74: GOOD (Still usable!)
⭐ 55-64: ACCEPTABLE

✅ DO score 75-85 for SOLID, USABLE clips (this is normal!)
✅ DO be optimistic - if it's theme-relevant with decent hook, go 70+
✅ REMEMBER: A 75-score clip can still go viral on TikTok!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "video_theme_analysis": "<1-2 sentence summary>",
  "top_clips": [
    // ⚠️ MUST CONTAIN EXACTLY {total_clips} OBJECTS!
    {{
      "rank": 1,
      "start_time": <timestamp>,
      "end_time": <timestamp>,
      "duration": <seconds>,
      "hook_text": "<exact first 3 seconds text>",
      "content_summary": "<what the full 30-60s covers>",
      "theme_relevance": "<how this addresses main topic>",
      "reason": "<why viral AND theme-relevant>",
      "viral_score": <70-100>,
      "category": "hook|emotional|value|controversial|storytelling",
      "suggested_caption": "<catchy caption>",
      "loop_hint": "<how to loop or N/A>"
    }},
    // ... continue until rank {total_clips}
  ]
}}

⚠️ FINAL REMINDERS:
1. Your response MUST include EXACTLY {total_clips} clips in top_clips array
2. If you cannot find {total_clips} perfect clips, provide {total_clips} best available
3. Lower-quality clips (score 65-75) are acceptable to meet the {total_clips} requirement
4. Count your clips before submitting - MUST BE EXACTLY {total_clips}!

Return ONLY the JSON (no markdown, no extra text):"""
        
        return prompt
    
    def _parse_and_validate_response(
        self, 
        response, 
        transcript: List[Dict], 
        video_duration: float,
        target_duration: int,
        expected_clips: int = 5  # 🆕 Expected count
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
        
        # Log theme analysis
        if "video_theme_analysis" in result:
            self.logger.info(f"📊 Theme Analysis: {result['video_theme_analysis']}")
        
        clips = result["top_clips"]
        
        if not isinstance(clips, list):
            raise ValueError("'top_clips' must be a list")
        
        # 🆕 Check clip count
        if len(clips) < expected_clips:
            self.logger.warning(
                f"⚠️ Gemini returned only {len(clips)} clips, expected {expected_clips}"
            )
        
        # 🆕 Process up to expected count (not hardcoded 5)
        clips_to_process = clips[:expected_clips]
        self.logger.info(f"Processing {len(clips_to_process)} clips from Gemini response")
        
        # Validate clips
        valid_clips = []
        seen_hooks = set()
        
        for i, clip in enumerate(clips_to_process):
            try:
                # Required fields
                required = ["rank", "start_time", "end_time", "hook_text", 
                           "reason", "viral_score", "category", "suggested_caption"]
                
                missing = [f for f in required if f not in clip]
                if missing:
                    self.logger.warning(f"Clip {i+1} missing fields: {missing}, skipping")
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
                
                # Validate duration (20-70s range)
                if duration < 20:
                    end = min(start + target_duration, video_duration)
                    duration = end - start
                    clip["end_time"] = end
                elif duration > 70:
                    end = start + 60
                    duration = end - start
                    clip["end_time"] = end
                
                clip["duration"] = duration
                
                # Check duplicate hooks
                hook_key = clip["hook_text"].lower()[:50]
                if hook_key in seen_hooks:
                    self.logger.warning(f"Clip {i+1} duplicate hook, skipping")
                    continue
                seen_hooks.add(hook_key)
                
                # Validate score
                score = float(clip.get("viral_score", 70))
                clip["viral_score"] = max(50, min(100, score))
                
                # Ensure required fields
                if "theme_relevance" not in clip:
                    clip["theme_relevance"] = "Related to video theme"
                
                if "content_summary" not in clip:
                    clip["content_summary"] = "Valuable content"
                
                valid_clips.append(clip)
                
            except Exception as e:
                self.logger.warning(f"Clip {i+1} validation error: {e}")
                continue
        
        # 🆕 Check if we got enough clips
        min_required = max(3, int(expected_clips * 0.6))  # At least 60%
        if len(valid_clips) < min_required:
            raise ValueError(
                f"Only {len(valid_clips)} valid clips, need at least {min_required} "
                f"(60% of {expected_clips})"
            )
        
        # Fix overlaps
        self._fix_overlapping_clips(valid_clips)
        
        # Sort by score
        valid_clips.sort(key=lambda x: x["viral_score"], reverse=True)
        
        # 🆕 Take exactly what was requested
        final_clips = valid_clips[:expected_clips]
        
        # Re-rank
        for i, clip in enumerate(final_clips):
            clip["rank"] = i + 1
        
        result["top_clips"] = final_clips
        
        self.logger.info(f"✅ Validated {len(final_clips)}/{expected_clips} clips")
        
        return result
    
    def _fix_overlapping_clips(self, clips: List[Dict]):
        """Fix overlapping timestamps"""
        sorted_clips = sorted(clips, key=lambda x: x["start_time"])
        
        for i in range(len(sorted_clips) - 1):
            current = sorted_clips[i]
            next_clip = sorted_clips[i + 1]
            
            if current["end_time"] > next_clip["start_time"]:
                overlap = current["end_time"] - next_clip["start_time"]
                self.logger.warning(f"Overlap {overlap:.1f}s detected, fixing...")
                current["end_time"] = next_clip["start_time"] - 1
                current["duration"] = current["end_time"] - current["start_time"]
    
    def _fallback_analysis(
        self, 
        transcript: List[Dict], 
        video_duration: float,
        clip_duration: int,
        total_clips: int = 5  # 🆕 Dynamic
    ) -> Dict:
        """Fallback analysis with dynamic clip count"""
        self.logger.warning(f"⚠️ Using fallback analysis for {total_clips} clips")
        
        scored_segments = []
        
        for seg in transcript:
            text = seg.get('text', '').strip()
            words = text.split()
            
            if len(words) < 5:
                continue
            
            score = len(words) * 2
            
            keywords = ['jadi', 'sebenarnya', 'rahasia', 'penting', 'intinya',
                       'tips', 'cara', 'harus', 'kesalahan']
            
            for kw in keywords:
                if kw in text.lower():
                    score += 15
            
            scored_segments.append({
                'start': seg['start'],
                'text': text,
                'score': score
            })
        
        scored_segments.sort(key=lambda x: x['score'], reverse=True)
        
        clips = []
        used_ranges = []
        
        # 🆕 Generate requested number
        for i, seg in enumerate(scored_segments):
            if len(clips) >= total_clips:
                break
            
            start = seg['start']
            end = min(start + clip_duration, video_duration)
            
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
                "content_summary": f"Content segment ({len(seg['text'].split())} words)",
                "theme_relevance": "Fallback selection",
                "reason": f"Fallback analyzer (score: {seg['score']})",
                "viral_score": 70.0 - (i * 2),
                "category": "value",
                "suggested_caption": f"Insights #{i+1} 💡",
                "loop_hint": "N/A"
            })
            
            used_ranges.append((start, end))
        
        self.logger.info(f"Fallback generated {len(clips)}/{total_clips} clips")
        
        return {
            "video_theme_analysis": "Fallback analysis - theme not analyzed",
            "top_clips": clips
        }
    
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
                'theme_relevance': clip_data.get('theme_relevance', 'Theme-related'),
                'suggested_caption': clip_data['suggested_caption'],
                'reason': clip_data['reason'],
                'loop_hint': clip_data.get('loop_hint', 'N/A')
            })
        
        return clips