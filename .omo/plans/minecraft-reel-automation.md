# Minecraft Reel Automation Pipeline

## TL;DR (For humans)

Build a Python automation that generates 20-second Minecraft parkour reels. The pipeline: scrapes a story from r/AmITheAsshole → generates AI voice narration (female, 1.5x speed) → fetches relevant memes using Gemma 4 keyword extraction → composites everything with MoviePy (background video, memes, subtitles, sound effects) → outputs a ready-to-post reel.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REEL GENERATION PIPELINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Reddit     │───▶│  Gemma 4    │───▶│  Meme API   │    │
│  │   Scraper    │    │  Keyword    │    │  (D3vd)     │    │
│  │             │    │  Extractor  │    │             │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              STORY PROCESSOR                         │   │
│  │  - Truncate story to ~20s narration                  │   │
│  │  - Generate TTS audio (edge-tts, 1.5x speed)        │   │
│  │  - Generate word-level timestamps for subtitles     │   │
│  │  - Detect sound effect trigger points                │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              VIDEO COMPOSITOR (MoviePy)              │   │
│  │  Layer 1: Minecraft parkour video (20s, cropped 9:16)│  │
│  │  Layer 2: Memes (top, 1s intervals, 0.5s transitions)│  │
│  │  Layer 3: Subtitles (center, word-by-word)           │   │
│  │  Layer 4: Sound effects (at trigger points)          │   │
│  │  Layer 5: AI voice narration                         │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │  Output:    │                                           │
│  │  reel_*.mp4 │                                           │
│  └─────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Story Scraping | Reddit JSON API | Free, no auth for public subreddits |
| Keyword Extraction | Ollama + Gemma 4 | Local, fast, already installed |
| Meme Fetching | D3vd Meme API | Free, no auth, Reddit-based |
| TTS | edge-tts | Free, no API key, supports rate control |
| Video Editing | MoviePy 2.x | Python-native, supports compositing |
| Audio Processing | FFmpeg (via MoviePy) | Industry standard |
| Subtitles | edge-tts SRT output + MoviePy | Word-level timing |

## File Structure

```
minecraft reels/
├── .omo/
│   └── plans/
│       └── minecraft-reel-automation.md  (this file)
├── videoplayback.mp4                     (background video)
├── sound_effects/
│   ├── boom.mp3
│   ├── fart.mp3
│   ├── vine_boom.mp3
│   └── ... (user adds more)
├── output/
│   └── (generated reels go here)
├── src/
│   ├── __init__.py
│   ├── config.py                         (constants & settings)
│   ├── reddit_scraper.py                 (fetch AITA stories)
│   ├── keyword_extractor.py              (Gemma 4 keyword extraction)
│   ├── meme_fetcher.py                   (D3vd API integration)
│   ├── tts_generator.py                  (edge-tts voice generation)
│   ├── sound_effects.py                  (sound effect matching & insertion)
│   ├── video_compositor.py               (MoviePy video assembly)
│   └── main.py                           (orchestrator)
├── requirements.txt
└── run.py                                (entry point)
```

---

## Todos

### Phase 1: Project Setup

- [ ] 1.1 Create `requirements.txt` with dependencies
  - **File**: `requirements.txt`
  - **Contents**:
    ```
    moviepy>=2.0
    edge-tts>=7.0
    requests>=2.31
    Pillow>=10.0
    ```
  - **Acceptance**: `pip install -r requirements.txt` succeeds
  - **QA**: Run `pip install -r requirements.txt` and verify all packages install without errors

- [ ] 1.2 Create `src/config.py` with all constants
  - **File**: `src/config.py`
  - **Contents**:
    ```python
    # Video settings
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920
    VIDEO_FPS = 30
    REEL_DURATION = 20  # seconds
    
    # Meme settings
    MEME_API_URL = "https://meme-api.com/gimme"
    MEME_DISPLAY_DURATION = 1.0  # seconds per meme
    MEME_TRANSITION_DURATION = 0.5  # seconds
    
    # TTS settings
    TTS_VOICE = "en-US-JennyNeural"  # Female voice
    TTS_RATE = "+50%"  # 1.5x speed
    
    # Paths
    BACKGROUND_VIDEO = "videoplayback.mp4"
    SOUND_EFFECTS_DIR = "sound_effects"
    OUTPUT_DIR = "output"
    TEMP_DIR = "temp"
    
    # Subtitle settings
    SUBTITLE_FONT_SIZE = 60
    SUBTITLE_FONT = "Impact"
    SUBTITLE_COLOR = "white"
    SUBTITLE_STROKE_COLOR = "black"
    SUBTITLE_STROKE_WIDTH = 3
    ```
  - **Acceptance**: File exists and imports correctly
  - **QA**: Run `python -c "from src.config import *; print('Config loaded')"` from project root

- [ ] 1.3 Create directory structure
  - **Directories**: `src/`, `sound_effects/`, `output/`, `temp/`
  - **Acceptance**: All directories exist
  - **QA**: `ls -la` shows all directories

---

### Phase 2: Reddit Story Scraper

- [ ] 2.1 Create `src/reddit_scraper.py`
  - **File**: `src/reddit_scraper.py`
  - **Function**: `fetch_aita_story() -> dict`
  - **Logic**:
    1. Fetch top posts from `https://www.reddit.com/r/AmItheAsshole/top.json?t=day&limit=10`
    2. Filter for posts with "AITA" flair or title containing "AITA"
    3. Select a post with substantial body text (at least 200 chars)
    4. Truncate story to fit ~20 seconds of narration (~300 words at 150 wpm)
    5. Return `{"title": str, "body": str, "url": str}`
  - **Error Handling**: Retry up to 3 times, fallback to hardcoded sample story
  - **Acceptance**: Returns a valid story dict with title and body
  - **QA**: Run `python -c "from src.reddit_scraper import fetch_aita_story; print(fetch_aita_story())"` and verify output

---

### Phase 3: Keyword Extraction (Gemma 4)

- [ ] 3.1 Create `src/keyword_extractor.py`
  - **File**: `src/keyword_extractor.py`
  - **Function**: `extract_keywords(story_text: str) -> list[str]`
  - **Logic**:
    1. Send story to Ollama API at `http://localhost:11434/api/generate`
    2. Prompt: "Extract 5-10 keywords from this story for finding relevant memes. Return only comma-separated keywords, nothing else: {story_text}"
    3. Parse response into list of keywords
    4. Return keywords list
  - **Acceptance**: Returns list of 5-10 keyword strings
  - **QA**: Run with sample AITA story and verify keywords are relevant

---

### Phase 4: Meme Fetcher

- [ ] 4.1 Create `src/meme_fetcher.py`
  - **File**: `src/meme_fetcher.py`
  - **Function**: `fetch_memes(keywords: list[str], count: int = 20) -> list[dict]`
  - **Logic**:
    1. For each keyword, call `https://meme-api.com/gimme/{keyword}`
    2. Collect meme URLs (prefer images over GIFs for faster loading)
    3. Deduplicate by URL
    4. Return list of `{"url": str, "title": str}` dicts
    5. If keyword fetch fails, fallback to `https://meme-api.com/gimme/memes`
  - **Acceptance**: Returns list of meme dicts with valid URLs
  - **QA**: Run with sample keywords and verify URLs are accessible

---

### Phase 5: TTS Generator

- [ ] 5.1 Create `src/tts_generator.py`
  - **File**: `src/tts_generator.py`
  - **Function**: `generate_tts(story_text: str) -> tuple[str, str]`
  - **Logic**:
    1. Use edge-tts to generate audio with female voice at 1.5x speed
    2. Command: `edge-tts --text "{story}" --voice "en-US-JennyNeural" --rate "+50%" --write-media temp/narration.mp3 --write-subtitles temp/narration.srt`
    3. Parse SRT file to get word-level timestamps
    4. Trim narration to fit within 20 seconds
    5. Return (audio_path, srt_path)
  - **Acceptance**: Generates valid MP3 and SRT files
  - **QA**: Generate TTS for sample text, verify audio plays and SRT has timestamps

---

### Phase 6: Sound Effects Manager

- [ ] 6.1 Create `src/sound_effects.py`
  - **File**: `src/sound_effects.py`
  - **Function**: `detect_sfx_triggers(story_text: str) -> list[dict]`
  - **Logic**:
    1. Define trigger words/phrases mapped to sound effects:
       - "boom", "explosion", "destroyed" → `boom.mp3`
       - "fart", "stink", "smell" → `fart.mp3`
       - "shock", "disbelief", "what" → `vine_boom.mp3`
       - "slap", "hit", "punch" → `slap.mp3`
    2. Scan story text for trigger words
    3. Map trigger position to timestamp using SRT file
    4. Return list of `{"timestamp": float, "sfx_file": str}` dicts
  - **Acceptance**: Returns list of trigger points with valid timestamps
  - **QA**: Run with sample story containing trigger words, verify timestamps are within narration duration

---

### Phase 7: Video Compositor (Core)

- [ ] 7.1 Create `src/video_compositor.py` - Background Video Handler
  - **File**: `src/video_compositor.py`
  - **Function**: `prepare_background() -> VideoFileClip`
  - **Logic**:
    1. Load `videoplayback.mp4`
    2. Trim to first 20 seconds
    3. Crop to 9:16 aspect ratio (1080x1920)
    4. Resize to target resolution
    5. Return processed clip
  - **Acceptance**: Returns 20s clip at 1080x1920
  - **QA**: Generate temp video, verify resolution and duration

- [ ] 7.2 Create `src/video_compositor.py` - Meme Overlay
  - **File**: `src/video_compositor.py`
  - **Function**: `create_meme_overlay(memes: list[dict]) -> CompositeVideoClip`
  - **Logic**:
    1. Download each meme image to temp folder
    2. Create ImageClip for each meme (1s duration)
    3. Position memes in top 40% of screen
    4. Add 0.5s crossfade between memes
    5. Chain memes sequentially for 20 seconds
    6. Return composite clip
  - **Acceptance**: Meme overlay spans 20s with smooth transitions
  - **QA**: Generate meme overlay video, verify transitions are smooth

- [ ] 7.3 Create `src/video_compositor.py` - Subtitle Overlay
  - **File**: `src/video_compositor.py`
  - **Function**: `create_subtitle_overlay(srt_path: str) -> CompositeVideoClip`
  - **Logic**:
    1. Parse SRT file for word timestamps
    2. Create TextClip for each word/phrase
    3. Position subtitles in center of screen
    4. Use Impact font, white with black stroke
    5. Sync with narration timing
    6. Return subtitle clip
  - **Acceptance**: Subtitles appear in sync with audio
  - **QA**: Generate video with subtitles, verify timing matches audio

- [ ] 7.4 Create `src/video_compositor.py` - Sound Effects Mixer
  - **File**: `src/video_compositor.py`
  - **Function**: `mix_audio(narration_path: str, sfx_triggers: list[dict]) -> AudioFileClip`
  - **Logic**:
    1. Load narration audio
    2. Load each sound effect file
    3. Place sound effects at trigger timestamps
    4. Mix all audio tracks together
    5. Ensure total duration ≤ 20 seconds
    6. Return mixed audio clip
  - **Acceptance**: Audio plays with narration + sound effects at correct times
  - **QA**: Generate mixed audio, verify sound effects play at expected moments

- [ ] 7.5 Create `src/video_compositor.py` - Final Composition
  - **File**: `src/video_compositor.py`
  - **Function**: `compose_reel(background, memes, subtitles, audio) -> str`
  - **Logic**:
    1. Create CompositeVideoClip with all layers:
       - Layer 1: Background video
       - Layer 2: Meme overlay (top 40%)
       - Layer 3: Subtitles (center)
    2. Set mixed audio as the clip's audio
    3. Write to output file: `output/reel_{timestamp}.mp4`
    4. Use codec: libx264, audio: aac
    5. Return output path
  - **Acceptance**: Generates valid 20s MP4 reel
  - **QA**: Play generated reel, verify all elements present and synced

---

### Phase 8: Main Orchestrator

- [ ] 8.1 Create `src/main.py`
  - **File**: `src/main.py`
  - **Function**: `generate_reel() -> str`
  - **Logic**:
    1. Fetch story from Reddit
    2. Extract keywords with Gemma 4
    3. Fetch memes based on keywords
    4. Generate TTS narration
    5. Detect sound effect triggers
    6. Compose video with all elements
    7. Cleanup temp files
    8. Return output path
  - **Error Handling**: Try/except with meaningful error messages
  - **Acceptance**: End-to-end generates a reel
  - **QA**: Run full pipeline, verify output video exists and plays

- [ ] 8.2 Create `run.py` entry point
  - **File**: `run.py`
  - **Logic**:
    ```python
    from src.main import generate_reel
    
    if __name__ == "__main__":
        output = generate_reel()
        print(f"Reel generated: {output}")
    ```
  - **Acceptance**: `python run.py` generates a reel
  - **QA**: Run `python run.py` and verify output

---

## Dependencies Matrix

| Todo | Depends On | Parallelizable |
|------|------------|----------------|
| 1.1 | None | Yes |
| 1.2 | 1.1 | Yes |
| 1.3 | None | Yes |
| 2.1 | 1.2 | Yes |
| 3.1 | 1.2 | Yes |
| 4.1 | 1.2 | Yes |
| 5.1 | 1.2 | Yes |
| 6.1 | 1.2 | Yes |
| 7.1 | 1.2 | Yes |
| 7.2 | 4.1 | Yes |
| 7.3 | 5.1 | Yes |
| 7.4 | 5.1, 6.1 | Yes |
| 7.5 | 7.1, 7.2, 7.3, 7.4 | No (final assembly) |
| 8.1 | 7.5 | No (orchestrator) |
| 8.2 | 8.1 | No |

**Critical Path**: 1.2 → 5.1 → 7.3 → 7.5 → 8.1 → 8.2

---

## Verification Strategy

**Test-After Approach**: Each todo includes acceptance criteria and QA steps.

**End-to-End QA**:
1. Run `python run.py` from project root
2. Verify `output/reel_*.mp4` is created
3. Play video and check:
   - Minecraft parkour background (20s, 9:16)
   - Memes change every 1 second
   - Subtitles appear in center, synced with audio
   - AI voice is female, fast (1.5x)
   - Sound effects play at appropriate moments

**Failure Scenarios**:
- Reddit API down → Use hardcoded sample story
- Meme API fails → Use random memes from `/gimme/memes`
- Ollama not running → Skip keyword extraction, use generic memes
- Sound effects folder empty → Skip SFX, only play narration

---

## Open Questions

None - all decisions made based on user input and research.
