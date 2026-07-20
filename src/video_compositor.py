"""Video compositor for assembling the Minecraft reel."""

import os
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    AudioClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
)

from .config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    REEL_DURATION,
    BACKGROUND_VIDEO,
    BACKGROUND_SPEED,
    MEME_POSITION_Y,
    MEME_MAX_HEIGHT,
    MEME_DISPLAY_DURATION,
    TEMP_DIR,
    OUTPUT_DIR,
    SOUND_EFFECTS_DIR,
)
from .subtitler import subtitle_video


def prepare_background() -> VideoFileClip:
    """Load and prepare the Minecraft parkour background video."""
    print("Preparing background video...")
    
    clip = VideoFileClip(BACKGROUND_VIDEO)
    
    original_width, original_height = clip.size
    target_ratio = 9 / 16
    current_ratio = original_width / original_height
    
    if current_ratio > target_ratio:
        new_width = int(original_height * target_ratio)
        x_center = original_width // 2
        clip = clip.cropped(
            x_center - new_width // 2,
            0,
            x_center + new_width // 2,
            original_height,
        )
    else:
        new_height = int(original_width / target_ratio)
        y_center = original_height // 2
        clip = clip.cropped(
            0,
            y_center - new_height // 2,
            original_width,
            y_center + new_height // 2,
        )
    
    clip = clip.resized((VIDEO_WIDTH, VIDEO_HEIGHT))
    
    if BACKGROUND_SPEED != 1.0:
        clip = clip.with_speed_scaled(BACKGROUND_SPEED)
    
    print(f"Background prepared: {clip.size}")
    return clip


def create_meme_overlay(meme_data: List[tuple]) -> CompositeVideoClip:
    """Create overlay of memes with variable durations.
    
    Args:
        meme_data: List of tuples (meme_path, duration_seconds)
    """
    print(f"Creating meme overlay with {len(meme_data)} memes...")
    
    if not meme_data:
        placeholder = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0))
        placeholder = placeholder.with_duration(1)
        return placeholder
    
    meme_clips = []
    
    for meme_path, meme_duration in meme_data:
        try:
            meme = ImageClip(meme_path)
            
            img_width, img_height = meme.size
            meme_width = 550
            meme_height = int(img_height * (meme_width / img_width))
            
            if meme_height > MEME_MAX_HEIGHT:
                meme_height = MEME_MAX_HEIGHT
                meme_width = int(img_width * (meme_height / img_height))
            
            meme = meme.resized((meme_width, meme_height))
            meme = meme.with_duration(meme_duration)
            
            meme_clips.append(meme)
            
        except Exception as e:
            print(f"Error loading meme {meme_path}: {e}")
            continue
    
    if not meme_clips:
        placeholder = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0))
        placeholder = placeholder.with_duration(1)
        return placeholder
    
    final_memes = concatenate_videoclips(
        meme_clips,
        method="compose",
        padding=0,
    )
    
    meme_x = (VIDEO_WIDTH - meme_width) // 2
    final_memes = final_memes.with_position((meme_x, MEME_POSITION_Y))
    
    print(f"Meme overlay created: {final_memes.duration}s")
    return final_memes


def create_subtitle_overlay(subtitle_entries: List[Dict]) -> CompositeVideoClip:
    """Create subtitle text overlay - placeholder, actual subs burned via ffmpeg."""
    placeholder = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0, 0))
    placeholder = placeholder.with_duration(0.1)
    return placeholder


def mix_sound_effects(sfx_data: List[tuple], duration: float) -> Optional[AudioFileClip]:
    """Mix sound effects into a single audio track at 25% volume."""
    if not sfx_data:
        return None
    
    print(f"Mixing {len(sfx_data)} sound effects...")
    
    audio_clips = []
    
    for filename, timestamp in sfx_data:
        try:
            sfx_path = os.path.join(SOUND_EFFECTS_DIR, filename)
            if not os.path.exists(sfx_path):
                print(f"  SFX not found: {filename}")
                continue
            
            sfx = AudioFileClip(sfx_path)
            sfx = sfx.with_volume_scaled(0.25)
            
            if timestamp + sfx.duration > duration:
                sfx = sfx.subclipped(0, duration - timestamp)
            
            sfx = sfx.with_start(timestamp)
            
            audio_clips.append(sfx)
            print(f"  Added: {filename} at {timestamp:.1f}s")
            
        except Exception as e:
            print(f"  Error loading SFX {filename}: {e}")
            continue
    
    if not audio_clips:
        return None
    
    from moviepy import CompositeAudioClip
    mixed_sfx = CompositeAudioClip(audio_clips)
    
    print(f"SFX mixed: {len(audio_clips)} effects")
    return mixed_sfx


def mix_audio(narration_path: str, sfx_data: List[tuple] = None) -> Tuple[AudioFileClip, Optional[AudioFileClip]]:
    """Load narration audio and optionally mix sound effects."""
    print("Loading narration...")
    narration = AudioFileClip(narration_path)
    
    sfx_track = None
    if sfx_data:
        sfx_track = mix_sound_effects(sfx_data, narration.duration)
    
    return narration, sfx_track


def compose_reel(
    background: VideoFileClip,
    memes: List[tuple],
    subtitles: List[Dict],
    narration_path: str,
    sfx_data: List[tuple] = None,
    title: str = None,
    thumbnail_path: str = None,
) -> str:
    """Compose the final reel from all components."""
    print("Composing final reel...")
    
    meme_overlay = create_meme_overlay(memes)
    narration, sfx_track = mix_audio(narration_path, sfx_data)
    
    duration = narration.duration
    
    background = background.subclipped(0, duration)
    
    if isinstance(meme_overlay, VideoFileClip):
        meme_overlay = meme_overlay.subclipped(0, duration)
    
    temp_output = os.path.join(TEMP_DIR, "temp_nosub.mp4")
    
    if title:
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        safe_title = safe_title[:50]
        if not safe_title:
            safe_title = "reel"
        final_output = os.path.join(OUTPUT_DIR, f"{safe_title}.mp4")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_output = os.path.join(OUTPUT_DIR, f"reel_{timestamp}.mp4")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        thumbnail_clip = ImageClip(thumbnail_path).with_duration(1 / VIDEO_FPS)
        if sfx_track:
            from moviepy import CompositeAudioClip
            silent_audio = AudioClip(lambda t: [0], duration=1 / VIDEO_FPS)
            thumbnail_clip = thumbnail_clip.with_audio(silent_audio)
        base_video = concatenate_videoclips([thumbnail_clip, background], method="compose")
        has_thumbnail = True
    else:
        base_video = background
        has_thumbnail = False
    
    if isinstance(meme_overlay, VideoFileClip):
        if has_thumbnail:
            meme_overlay = meme_overlay.with_start(1 / VIDEO_FPS)
        temp_video = CompositeVideoClip([base_video, meme_overlay])
    elif hasattr(meme_overlay, 'with_duration'):
        meme_overlay = meme_overlay.with_duration(base_video.duration)
        if has_thumbnail:
            meme_overlay = meme_overlay.with_start(1 / VIDEO_FPS)
        temp_video = CompositeVideoClip([base_video, meme_overlay])
    else:
        temp_video = base_video
    
    temp_video = temp_video.with_duration(base_video.duration)
    
    if sfx_track:
        from moviepy import CompositeAudioClip
        combined_audio = CompositeAudioClip([narration, sfx_track])
        temp_video = temp_video.with_audio(combined_audio)
    else:
        temp_video = temp_video.with_audio(narration)
    
    print(f"Rendering {base_video.duration:.1f}s video...")
    temp_video.write_videofile(
        temp_output,
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="5000k",
        preset="medium",
        threads=4,
    )
    
    temp_video.close()
    background.close()
    narration.close()
    if sfx_track:
        sfx_track.close()
    
    print("Adding subtitles...")
    subtitle_offset = 1 / VIDEO_FPS if has_thumbnail else 0.0
    subtitle_video(temp_output, subtitles, final_output, offset=subtitle_offset)
    
    if os.path.exists(temp_output):
        os.remove(temp_output)
    
    print(f"Reel created: {final_output}")
    return final_output
