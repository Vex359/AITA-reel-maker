# Fix Meme Size and Position

## TL;DR
The meme is currently 980px wide (90% of screen) and positioned at Y=500 (near top). Need to reduce to ~400px wide (medium) and center vertically at Y=800 (above subtitles).

## Problem
- Screenshot shows meme taking up nearly the entire screen width
- Meme is at the top, not centered
- User wants "normal medium sized meme" in the center, above subtitles

## Changes Required

### 1. `src/config.py` - Line 36
```python
# Before:
MEME_POSITION_Y = 500

# After:
MEME_POSITION_Y = 800  # Center of 1920 height, above subtitles at bottom
```

### 2. `src/video_compositor.py` - Lines 83-88
```python
# Before:
img_width, img_height = meme.size
meme_width = VIDEO_WIDTH - 100  # 980px = 90% of screen - TOO BIG
meme_height = int(img_height * (meme_width / img_width))

if meme_height > MEME_MAX_HEIGHT:
    meme_height = MEME_MAX_HEIGHT
    meme_width = int(img_width * (meme_height / img_height))

# After:
img_width, img_height = meme.size
meme_width = 400  # Medium size = 37% of screen width
meme_height = int(img_height * (meme_width / img_width))

if meme_height > MEME_MAX_HEIGHT:
    meme_height = MEME_MAX_HEIGHT
    meme_width = int(img_width * (meme_height / img_height))
```

## Expected Result
- Meme: ~400px wide (medium size, not huge)
- Meme: Centered at Y=800 (middle of screen, above subtitles)
- Subtitles: Remain at bottom (Alignment=2, MarginV=150)

## Verification
1. Run `python -m src.main`
2. Check output video shows:
   - Meme at medium size (not taking up full width)
   - Meme centered vertically
   - Subtitles at bottom
