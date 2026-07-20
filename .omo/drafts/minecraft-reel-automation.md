# Draft: Minecraft Reel Automation

## Intent: CLEAR
The user wants a complete automation pipeline to generate 20-second Minecraft parkour reels with Reddit stories, memes, AI voice, subtitles, and sound effects.

## Review Required: No
Standard plan, no high-accuracy review requested.

## Key Decisions
- **Meme API**: Free D3vd Meme API (meme-api.com/gimme) - no auth needed
- **AI Voice**: edge-tts female voice (en-US-JennyNeural) at 1.5x speed
- **Local LLM**: Ollama + Gemma 4 (already installed)
- **Sound Effects**: User will create folder later, use placeholder structure
- **Video Composition**: MoviePy + FFmpeg
- **Story Source**: Reddit r/AmITheAsshole via JSON API

## Research Findings
- D3vd Meme API: `https://meme-api.com/gimme` returns random memes, can specify subreddit
- edge-tts: Free TTS, supports rate adjustment (+50% for 1.5x), has female voices like en-US-JennyNeural
- Gemma 4 via Ollama: API at localhost:11434, can extract keywords from story text
- MoviePy: Python video editing, supports compositing, text overlays, audio mixing
- Reddit JSON API: Append .json to any Reddit URL (may have challenge walls now)

## Status: awaiting-approval
Plan ready to be written after user approves approach.
