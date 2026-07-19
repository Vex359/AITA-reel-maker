# AITA Reel Maker

Automates creation of TikTok-style Minecraft parkour reels with Reddit stories, memes, AI voice narration, sound effects, and karaoke subtitles.

## What It Does

Takes a story (or generates one from AITA-style Reddit posts) and produces a complete vertical video with:

- **Minecraft parkour background** (1.5x speed, 9:16 format)
- **AI voice narration** (cringey high-pitched Gen Z voice)
- **Meme overlays** (context-aware, variable duration)
- **Sound effects** (LLM-selected, synced to narration)
- **Karaoke subtitles** (word-by-word yellow highlight)
- **Thumbnail** (Minecraft bg + hook text + meme)

## How It Works

1. **Script Generation** — LLM writes a Gen Z narration script with mandatory pauses
2. **TTS** — Edge-TTS generates narration with pitch-shifted voice
3. **Meme Selection** — LLM picks memes from local folder based on script context
4. **SFX Selection** — LLM picks 3-5 sound effects with precise timestamps
5. **Thumbnail** — Extracts Minecraft frame, overlays hook text + random meme
6. **Composition** — MoviePy assembles everything, ffmpeg burns ASS subtitles

## Setup

### Requirements

- Python 3.10+
- ffmpeg (in PATH)
- OpenRouter API key (for LLM)

### Install

```bash
pip install moviepy edge-tts openai Pillow requests
```

### Configure

Set your OpenRouter API key in `src/keyword_extractor.py`:

```python
OPENROUTER_API_KEY = "your-key-here"
```

### Run

**Streamlit UI:**
```bash
cd "minecraft reels"
streamlit run app.py
```

**Direct:**
```bash
python -m src.main
```

## Project Structure

```
minecraft reels/
├── src/
│   ├── config.py           # Constants, prompts
│   ├── main.py             # Pipeline orchestrator
│   ├── keyword_extractor.py # LLM script generation
│   ├── tts_generator.py    # Edge-TTS voice
│   ├── meme_fetcher.py     # Local meme selection
│   ├── video_compositor.py # Video assembly
│   ├── subtitler.py        # ASS/karaoke subtitles
│   ├── thumbnail.py        # Thumbnail generation
│   └── reddit_scraper.py   # Fallback stories
├── Memes/                  # Your meme collection (10 categories)
├── sound effects/          # SFX files
├── videoplayback.mp4       # Minecraft background video
└── app.py                  # Streamlit UI
```

## Customization

- **Voice**: Edit `TTS_VOICE`, `TTS_RATE`, `TTS_PITCH` in `config.py`
- **Memes**: Add to `Memes/` folder in category subfolders
- **SFX**: Add `.mp3` files to `sound effects/`
- **Subtitle style**: Edit ASS style in `subtitler.py`
