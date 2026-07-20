"""Thumbnail generator for hook-worthy video intros."""

import os
import random
from PIL import Image, ImageDraw, ImageFont
import subprocess


THUMBNAIL_WIDTH = 1080
THUMBNAIL_HEIGHT = 1920
THUMBNAIL_FONTSIZE = 80

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC_BACKGROUND = os.path.join(BASE_DIR, "temp", "mc_background.png")
VIDEO_PATH = os.path.join(BASE_DIR, "videoplayback.mp4")
MEMES_DIR = os.path.join(BASE_DIR, "Memes")

HOOK_PROMPT = """Generate a SHORT, controversial hook text for a video thumbnail.
This text will appear for a split second at the start of the video to grab attention.
It should be shocking, controversial, or make people want to keep watching.

Story/Script:
{story}

Return ONLY the hook text (max 5 words), nothing else.
Examples of good hooks:
- "HE DIDN'T DESERVE THIS"
- "SHE DESTROYED HIM"
- "WAIT FOR THE END"
"""


def generate_hook_text(story: str) -> str:
    try:
        from .keyword_extractor import call_llm
        prompt = HOOK_PROMPT.format(story=story)
        hook = call_llm(prompt)
        if hook and len(hook) <= 30:
            return hook.upper()
    except Exception:
        pass
    return "WATCH THIS"


def get_random_meme():
    categories = [d for d in os.listdir(MEMES_DIR) if os.path.isdir(os.path.join(MEMES_DIR, d))]
    if not categories:
        return None
    
    cat = random.choice(categories)
    cat_path = os.path.join(MEMES_DIR, cat)
    memes = [f for f in os.listdir(cat_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    
    if not memes:
        return None
    
    return os.path.join(cat_path, random.choice(memes))


def ensure_mc_background():
    """Extract Minecraft background from video if not present."""
    if os.path.exists(MC_BACKGROUND):
        return True
    
    if not os.path.exists(VIDEO_PATH):
        print(f"Warning: Video file not found: {VIDEO_PATH}")
        return False
    
    os.makedirs(os.path.dirname(MC_BACKGROUND), exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-ss", "5",
        "-i", VIDEO_PATH,
        "-frames:v", "1",
        MC_BACKGROUND,
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"Extracted Minecraft background from video")
        return os.path.exists(MC_BACKGROUND)
    except Exception as e:
        print(f"Warning: Failed to extract background: {e}")
        return False


def create_thumbnail(hook_text: str, meme_path: str = None) -> Image.Image:
    ensure_mc_background()
    
    if os.path.exists(MC_BACKGROUND):
        img = Image.open(MC_BACKGROUND).copy()
        img = img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
    else:
        img = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), color=(0, 0, 0))
    
    overlay = Image.new("RGBA", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), (0, 0, 0, 0))
    
    if meme_path and os.path.exists(meme_path):
        try:
            meme = Image.open(meme_path).convert("RGBA")
            meme_width = int(THUMBNAIL_WIDTH * 0.6)
            meme_height = int(meme.height * (meme_width / meme.width))
            meme = meme.resize((meme_width, meme_height), Image.LANCZOS)
            meme_x = (THUMBNAIL_WIDTH - meme_width) // 2
            meme_y = THUMBNAIL_HEIGHT // 3 - meme_height // 2
            
            bg_overlay = Image.new("RGBA", meme.size, (0, 0, 0, 180))
            overlay.paste(bg_overlay, (meme_x, meme_y))
            overlay.paste(meme, (meme_x, meme_y), meme)
        except Exception:
            pass
    
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("impact.ttf", THUMBNAIL_FONTSIZE)
    except OSError:
        try:
            font = ImageFont.truetype(
                os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "impact.ttf"),
                THUMBNAIL_FONTSIZE
            )
        except OSError:
            font = ImageFont.load_default()
    
    words = hook_text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] > THUMBNAIL_WIDTH - 100:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    
    if not lines:
        lines = [hook_text]
    
    total_height = len(lines) * (THUMBNAIL_FONTSIZE + 20)
    y_start = int(THUMBNAIL_HEIGHT * 0.65)
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (THUMBNAIL_WIDTH - text_width) // 2
        y = y_start + i * (THUMBNAIL_FONTSIZE + 20)
        
        draw.text((x + 4, y + 4), line, fill=(0, 0, 0), font=font)
        draw.text((x, y), line, fill=(255, 255, 0), font=font)
    
    return img.convert("RGB")


def save_thumbnail(img: Image.Image, output_path: str) -> str:
    img.save(output_path, "PNG")
    return output_path


def generate_thumbnail(story: str, temp_dir: str) -> tuple:
    hook_text = generate_hook_text(story)
    print(f"Thumbnail hook: {hook_text}")
    
    meme_path = get_random_meme()
    img = create_thumbnail(hook_text, meme_path)
    thumb_path = os.path.join(temp_dir, "thumbnail.png")
    save_thumbnail(img, thumb_path)
    
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    save_thumbnail(img, os.path.join(output_dir, "last_thumbnail.png"))
    
    return thumb_path, hook_text