"""Main orchestrator for Minecraft Reel Automation pipeline."""

import os
import shutil
from typing import Optional

from .config import TEMP_DIR, OUTPUT_DIR
from .reddit_scraper import fetch_aita_story, truncate_story
from .keyword_extractor import generate_script, extract_keywords, generate_absurd_script
from .meme_fetcher import fetch_and_download_memes, select_sfx_with_llm
from .tts_generator import generate_tts
from .video_compositor import prepare_background, compose_reel
from .thumbnail import generate_thumbnail


def cleanup_temp():
    """Clean up temporary files with retry for Windows file locking."""
    import time
    import gc
    
    gc.collect()
    
    if os.path.exists(TEMP_DIR):
        for attempt in range(3):
            try:
                shutil.rmtree(TEMP_DIR)
                break
            except PermissionError:
                time.sleep(0.5)
        os.makedirs(TEMP_DIR, exist_ok=True)


def generate_reel() -> str:
    """Generate a complete Minecraft parkour reel.
    
    Returns:
        Path to the generated video file
        
    Raises:
        Exception: If any step fails critically
    """
    print("=" * 60)
    print("MINECRAFT REEL AUTOMATION")
    print("=" * 60)
    
    try:
        print("\n[1/8] Fetching story...")
        story = fetch_aita_story()
        story = truncate_story(story, max_words=200)
        print(f"  Story: {story['title'][:60]}")
        
        print("\n[2/8] Generating script...")
        script = generate_script(story["body"])
        print(f"  Script: {script[:50]}...")
        
        print("\n[3/8] Extracting keywords...")
        keywords = extract_keywords(script)
        
        print("\n[4/8] Generating voice narration...")
        narration_path, subtitles = generate_tts(script)
        print(f"  Narration: {narration_path}")
        print(f"  Subtitles: {len(subtitles)} phrases")
        
        print("\n[5/8] Fetching memes...")
        memes = fetch_and_download_memes(keywords, count=20, script=script, subtitles=subtitles)
        print(f"  Downloaded {len(memes)} memes")
        
        print("\n[6/8] Selecting sound effects...")
        from .tts_generator import get_audio_duration
        narration_duration = get_audio_duration(narration_path)
        sfx_data = select_sfx_with_llm(script, subtitles, duration=narration_duration)
        print(f"  Selected {len(sfx_data)} sound effects")
        
        print("\n[7/8] Generating thumbnail hook...")
        thumbnail_path, hook_text = generate_thumbnail(script, TEMP_DIR)
        
        print("\n[8/8] Composing final video...")
        background = prepare_background()
        
        output_path = compose_reel(
            background=background,
            memes=memes,
            subtitles=subtitles,
            narration_path=narration_path,
            sfx_data=sfx_data,
            title=hook_text,
            thumbnail_path=thumbnail_path,
        )
        
        cleanup_temp()
        
        print("\n" + "=" * 60)
        print(f"REEL GENERATED SUCCESSFULLY!")
        print(f"Output: {output_path}")
        print("=" * 60)
        
        return output_path
        
    except Exception as e:
        print(f"\nERROR: {e}")
        cleanup_temp()
        raise


def generate_reel_with_story(story_text: str, title: str = "Custom Story") -> str:
    """Generate a reel with a custom story (for testing)."""
    print("=" * 60)
    print("MINECRAFT REEL - CUSTOM STORY MODE")
    print("=" * 60)
    
    story = {"title": title, "body": story_text, "url": "custom"}
    
    script = generate_script(story_text)
    keywords = extract_keywords(script)
    narration_path, subtitles = generate_tts(script)
    
    memes = fetch_and_download_memes(keywords, count=20, script=script, subtitles=subtitles)
    
    from .tts_generator import get_audio_duration
    narration_duration = get_audio_duration(narration_path)
    sfx_data = select_sfx_with_llm(script, subtitles, duration=narration_duration)
    
    thumbnail_path, hook_text = generate_thumbnail(script, TEMP_DIR)
    
    background = prepare_background()
    
    output_path = compose_reel(
        background=background,
        memes=memes,
        subtitles=subtitles,
        narration_path=narration_path,
        sfx_data=sfx_data,
        title=hook_text,
        thumbnail_path=thumbnail_path,
    )
    
    cleanup_temp()
    return output_path


def generate_absurd_reel(topic: str = "", title: str = "AI Absurd") -> str:
    """Generate a reel with an absurd AI-generated script."""
    print("=" * 60)
    print("MINECRAFT REEL - AI ABSURD MODE")
    print("=" * 60)
    
    script = generate_absurd_script(topic)
    print(f"  Script: {script[:80]}...")
    
    keywords = extract_keywords(script)
    narration_path, subtitles = generate_tts(script)
    
    memes = fetch_and_download_memes(keywords, count=20, script=script, subtitles=subtitles)
    
    from .tts_generator import get_audio_duration
    narration_duration = get_audio_duration(narration_path)
    sfx_data = select_sfx_with_llm(script, subtitles, duration=narration_duration)
    
    thumbnail_path, hook_text = generate_thumbnail(script, TEMP_DIR)
    
    background = prepare_background()
    
    output_path = compose_reel(
        background=background,
        memes=memes,
        subtitles=subtitles,
        narration_path=narration_path,
        sfx_data=sfx_data,
        title=hook_text,
        thumbnail_path=thumbnail_path,
    )
    
    cleanup_temp()
    return output_path
