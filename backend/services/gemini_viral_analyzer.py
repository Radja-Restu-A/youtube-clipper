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
        max_retries: int = 3,
        timeout: int = 45
    ) -> Dict:
        """
        Analyze video and find top 5 viral clips that match video theme
        
        Args:
            youtube_url: YouTube URL
            video_title: Video title (for context)
            video_description: Video description (for context)
            video_duration: Total duration
            transcript: Full transcript
            language: Language code
            clip_duration: Target clip length
            max_retries: Retry attempts
            timeout: Request timeout
        
        Returns:
            Dict with top_clips array
        """
        self.logger.info(f"🔍 Analyzing viral segments for: {video_title}")
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
            clip_duration=clip_duration
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
                
                self.logger.info(f"✅ Analysis complete! {len(result['top_clips'])} theme-relevant clips")
                
                # Log clips with relevance scores
                for i, clip in enumerate(result['top_clips']):
                    self.logger.info(
                        f"  🔥 Clip {i+1}: {clip['start_time']:.1f}s-{clip['end_time']:.1f}s | "
                        f"Score: {clip['viral_score']:.1f} | "
                        f"Relevance: {clip.get('theme_relevance', 'N/A')} | "
                        f"{clip['category']}"
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
    
    def _build_context_aware_prompt(
        self,
        youtube_url: str,
        video_title: str,
        video_description: str,
        video_duration: float,
        transcript: List[Dict],
        language: str,
        clip_duration: int
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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FULL TRANSCRIPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{transcript_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 YOUR MISSION:

Analyze this video holistically and find the TOP 5 viral-worthy clips that:

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

EXAMPLE SCORING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Clip: "Jadi kesalahan terbesar di [THEME] adalah..."
- Theme Relevance: 90 (directly addresses title topic)
- Hook Quality: 85 (strong curiosity hook)
- Content Value: 75 (delivers specific examples)
- Virality: 70 (likely to get comments)

viral_score = (90×0.30) + (85×0.35) + (75×0.20) + (70×0.15)
            = 27 + 29.75 + 15 + 10.5
            = 82.25 → Score: 82 ✅ GREAT CLIP!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT TO AVOID:
❌ Off-topic tangents (even if entertaining)
❌ Generic intros not related to theme
❌ Filler conversations that don't address main topic
❌ CTAs and outros
❌ Segments that don't deliver on title's promise

DIVERSITY WITHIN THEME:
- All 5 clips should relate to the SAME main theme
- But cover DIFFERENT aspects/angles of that theme
- Example: If theme is "Business Tips"
  → Clip 1: Hook about mistake #1
  → Clip 2: Hook about success strategy
  → Clip 3: Hook about mindset shift
  → Clip 4: Hook about resource management
  → Clip 5: Hook about scaling tips

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TECHNICAL REQUIREMENTS:
✅ Each clip: 30-60 seconds (hook 3s + content 27-57s)
✅ Use EXACT timestamps from transcript
✅ NO overlapping clips
✅ 5 DIFFERENT segments covering different aspects of theme

SCORING (0-100) - BE GENEROUS BUT FAIR:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⭐ 85-100: EXCEPTIONAL
- Perfect hook that stops scrolling instantly
- Delivers massive value on theme
- Extremely shareable/comment-worthy
- Example: Reveals shocking secret about main topic

⭐ 75-84: VERY GOOD (Most viral clips fall here!)
- Strong hook related to theme
- Good content delivery
- Clear viral potential
- This is the TARGET range for quality clips

⭐ 65-74: GOOD (Still usable!)
- Decent hook about theme
- Valuable content
- Some viral elements
- Acceptable for selection

⭐ 55-64: ACCEPTABLE
- Theme-relevant with okay hook
- Basic value delivery
- Minimal viral potential

⚠️ Below 55: AVOID
- Weak theme connection
- Poor hook
- Low engagement potential

IMPORTANT CALIBRATION NOTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DO score 75-85 for SOLID, USABLE clips (this is normal!)
✅ DO be optimistic - if it's theme-relevant with decent hook, go 70+
✅ DON'T reserve 80+ only for "perfect" content
✅ DON'T be overly critical - real podcasts are conversational
✅ REMEMBER: A 75-score clip can still go viral on TikTok!

Think like a TikTok creator, not a film critic. 
If YOU would post this clip, score it 70+.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "video_theme_analysis": "<1-2 sentence summary of what this video is primarily about>",
  "top_clips": [
    {{
      "rank": 1,
      "start_time": <timestamp where hook starts>,
      "end_time": <start_time + 30 to 60 seconds>,
      "duration": <end_time - start_time>,
      "hook_text": "<exact first 3 seconds text that hooks viewers INTO THE THEME>",
      "content_summary": "<what the full 30-60s clip covers related to theme>",
      "theme_relevance": "<how this clip addresses the video's main topic>",
      "reason": "<why this hook+content combo is viral AND theme-relevant>",
      "viral_score": <70-100>,
      "category": "hook|emotional|value|controversial|storytelling",
      "suggested_caption": "<catchy caption that references the THEME>",
      "loop_hint": "<how to loop, or 'N/A'>"
    }}
  ]
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXAMPLE OUTPUT STRUCTURE:

{{
  "video_theme_analysis": "This video discusses common mistakes entrepreneurs make when starting online businesses, with focus on mindset and resource management.",
  "top_clips": [
    {{
      "rank": 1,
      "start_time": 145.2,
      "end_time": 190.5,
      "duration": 45.3,
      "hook_text": "Jadi kesalahan terbesar di bisnis online yang bikin 90% orang gagal adalah...",
      "content_summary": "Explains the biggest mistake (not validating market first), gives 3 real examples of failed businesses, and shows the correct approach with actionable steps",
      "theme_relevance": "Directly addresses main topic of business mistakes mentioned in title. Delivers specific mistake + solution that viewers came to learn",
      "reason": "Perfect hook about THE MISTAKE (aligns with video promise), then delivers valuable lesson with examples. Viewers searching for business mistakes will find exactly what they need. Will spark comments sharing their own mistakes",
      "viral_score": 95.0,
      "category": "value",
      "suggested_caption": "Kesalahan #1 yang bikin bisnis online gagal 😱 90% orang gak sadar lagi ngulang ini! #BisnisOnline #TipsUsaha",
      "loop_hint": "Ends with question about mistake #2, loops to wanting more"
    }}
  ]
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NOW ANALYZE:

🎯 CRITICAL INSTRUCTION FOR SCORING:
You are analyzing REAL podcast content, not Hollywood movies.
Most GOOD, VIRAL-WORTHY clips will score 75-85.
Don't be overly critical or conservative.

If a clip has:
✅ Clear connection to video theme → Give at least 70+ base
✅ Decent hook that creates curiosity → Add 5-10 points
✅ Delivers valuable content → Add 5-10 points
✅ Has viral elements → Add 5-10 points

A clip with all 4 should easily be 80-90, not 60-70!

STEP-BY-STEP PROCESS:

1. Identify video theme from title + description
2. Find 5 segments that BEST match the theme
3. For EACH segment, calculate detailed scores:
   
   Component Scores (each 0-100):
   - Theme Relevance: How well does it match title promise?
   - Hook Quality: How strong is the opening 3 seconds?
   - Content Value: How valuable is the full 30-60s?
   - Virality: How likely to get engagement?
   
4. Calculate weighted viral_score using formula above
5. Round to 1 decimal place
6. Ensure at least 2-3 clips score 75+

Remember: Be OPTIMISTIC but honest. Real creators would post these clips!

Return ONLY the JSON (no markdown, no extra text):"""
        
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
            raise
        
        if "top_clips" not in result:
            raise ValueError("Missing 'top_clips' in response")
        
        # Log theme analysis if present
        if "video_theme_analysis" in result:
            self.logger.info(f"📊 Theme Analysis: {result['video_theme_analysis']}")
        
        clips = result["top_clips"]
        
        if not isinstance(clips, list) or len(clips) < 3:
            raise ValueError(f"Need at least 3 clips, got {len(clips)}")
        
        # Validate clips
        valid_clips = []
        seen_hooks = set()
        
        for i, clip in enumerate(clips[:5]):
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
                
                # Ensure theme_relevance field
                if "theme_relevance" not in clip:
                    clip["theme_relevance"] = "Related to video theme"
                
                # Ensure content_summary
                if "content_summary" not in clip:
                    clip["content_summary"] = "Valuable content"
                
                valid_clips.append(clip)
                
            except Exception as e:
                self.logger.warning(f"Clip {i+1} validation error: {e}")
                continue
        
        if len(valid_clips) < 3:
            raise ValueError(f"Only {len(valid_clips)} valid clips")
        
        # Fix overlaps
        self._fix_overlapping_clips(valid_clips)
        
        # Sort by score
        valid_clips.sort(key=lambda x: x["viral_score"], reverse=True)
        
        # Re-rank
        for i, clip in enumerate(valid_clips):
            clip["rank"] = i + 1
        
        result["top_clips"] = valid_clips[:5]
        
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
        clip_duration: int
    ) -> Dict:
        """Fallback analysis"""
        self.logger.warning("⚠️ Using fallback analysis")
        
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
        
        for i, seg in enumerate(scored_segments):
            if len(clips) >= 5:
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
                "viral_score": 70.0 - (i * 3),
                "category": "value",
                "suggested_caption": f"Insights #{i+1} 💡",
                "loop_hint": "N/A"
            })
            
            used_ranges.append((start, end))
        
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