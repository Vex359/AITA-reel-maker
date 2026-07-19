"""TTS generator using edge-tts (free, no auth)."""

import asyncio
import os
import re
from typing import Tuple, List, Dict

from .config import (
    TTS_VOICE,
    TTS_RATE,
    TTS_VOLUME,
    TTS_PITCH,
    TEMP_DIR,
    REEL_DURATION,
    SUBTITLE_WORDS_PER_PHRASE,
)


def parse_srt(srt_path: str) -> List[Dict]:
    """Parse SRT subtitle file into structured data.
    
    Args:
        srt_path: Path to SRT file
        
    Returns:
        List of dicts with start_time, end_time, text
    """
    entries = []
    
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return entries
    
    # Split by double newline (SRT entries)
    blocks = content.strip().split("\n\n")
    
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        
        # Parse timestamp line
        timestamp_line = lines[1]
        match = re.match(
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
            timestamp_line,
        )
        
        if not match:
            continue
        
        groups = match.groups()
        start_time = (
            int(groups[0]) * 3600
            + int(groups[1]) * 60
            + int(groups[2])
            + int(groups[3]) / 1000
        )
        end_time = (
            int(groups[4]) * 3600
            + int(groups[5]) * 60
            + int(groups[6])
            + int(groups[7]) / 1000
        )
        
        text = " ".join(lines[2:])
        
        entries.append({
            "start_time": start_time,
            "end_time": end_time,
            "text": text,
        })
    
    return entries


def parse_vtt(vtt_path: str) -> List[Dict]:
    """Parse VTT subtitle file (edge-tts default output format).
    
    Args:
        vtt_path: Path to VTT file
        
    Returns:
        List of dicts with start_time, end_time, text
    """
    entries = []
    
    try:
        with open(vtt_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return entries
    
    # Remove WEBVTT header
    if content.startswith("WEBVTT"):
        content = content.split("\n", 2)[-1] if "\n" in content else ""
    
    # Split by double newline
    blocks = content.strip().split("\n\n")
    
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        
        # Find timestamp line
        timestamp_line = None
        text_start_idx = 0
        
        for i, line in enumerate(lines):
            if "-->" in line:
                timestamp_line = line
                text_start_idx = i + 1
                break
        
        if not timestamp_line:
            continue
        
        match = re.match(
            r"(\d{2}):(\d{2}):(\d{2})[.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.](\d{3})",
            timestamp_line,
        )
        
        if not match:
            continue
        
        groups = match.groups()
        start_time = (
            int(groups[0]) * 3600
            + int(groups[1]) * 60
            + int(groups[2])
            + int(groups[3]) / 1000
        )
        end_time = (
            int(groups[4]) * 3600
            + int(groups[5]) * 60
            + int(groups[6])
            + int(groups[7]) / 1000
        )
        
        text = " ".join(lines[text_start_idx:])
        
        entries.append({
            "start_time": start_time,
            "end_time": end_time,
            "text": text,
        })
    
    return entries


def group_words_into_phrases(
    entries: List[Dict], 
    words_per_phrase: int = 4,
    max_duration: float = None,
) -> List[Dict]:
    """Group individual word entries into subtitle phrases.
    
    Args:
        entries: List of word-level timestamp entries
        words_per_phrase: Number of words per subtitle phrase
        max_duration: Maximum duration in seconds
        
    Returns:
        List of phrase-level timestamp entries
    """
    if not entries:
        return []
    
    phrases = []
    current_words = []
    current_start = None
    
    for entry in entries:
        if current_start is None:
            current_start = entry["start_time"]
        
        current_words.append(entry["text"])
        
        if len(current_words) >= words_per_phrase:
            phrase_text = " ".join(current_words)
            phrase_end = entry["end_time"]
            
            phrases.append({
                "start_time": current_start,
                "end_time": phrase_end,
                "text": phrase_text,
            })
            
            current_words = []
            current_start = None
    
    # Handle remaining words
    if current_words:
        phrases.append({
            "start_time": current_start,
            "end_time": entries[-1]["end_time"],
            "text": " ".join(current_words),
        })
    
    # Limit duration if specified
    if max_duration:
        phrases = [p for p in phrases if p["start_time"] < max_duration]
        if phrases and phrases[-1]["end_time"] > max_duration:
            phrases[-1]["end_time"] = max_duration
    
    return phrases


async def generate_tts_async(text: str) -> Tuple[str, str]:
    """Generate TTS audio and subtitles asynchronously.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Tuple of (audio_path, subtitle_path)
    """
    import edge_tts
    
    audio_path = os.path.join(TEMP_DIR, "narration.mp3")
    subtitle_path = os.path.join(TEMP_DIR, "narration.vtt")
    
    communicate = edge_tts.Communicate(
        text,
        TTS_VOICE,
        rate=TTS_RATE,
        volume=TTS_VOLUME,
        pitch=TTS_PITCH,
    )
    
    submaker = edge_tts.SubMaker()
    
    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
    
    # Write subtitles
    with open(subtitle_path, "w", encoding="utf-8") as sub_file:
        sub_file.write(submaker.get_srt())
    
    return audio_path, subtitle_path


def generate_tts(text: str) -> Tuple[str, List[Dict]]:
    """Generate TTS audio and return audio path with subtitle timestamps.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Tuple of (audio_path, subtitle_entries)
    """
    print(f"Generating TTS for: {text[:50]}...")
    
    # Run async TTS generation
    audio_path, subtitle_path = asyncio.run(generate_tts_async(text))
    
    # Parse subtitles
    entries = parse_vtt(subtitle_path)
    
    if not entries:
        # Try parsing as SRT
        entries = parse_srt(subtitle_path)
    
    # Group words into phrases for better readability (2-3 words max)
    phrases = group_words_into_phrases(entries, words_per_phrase=SUBTITLE_WORDS_PER_PHRASE)
    
    print(f"Generated {len(phrases)} subtitle phrases")
    return audio_path, phrases


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(audio_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0.0
