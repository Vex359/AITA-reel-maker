"""Smart sound effects manager with LLM-based classification."""

import os
import json
import random
import time
import requests
from typing import List, Dict, Optional

from .config import (
    SOUND_EFFECTS_DIR,
    REEL_DURATION,
    OPENROUTER_API_URL,
    OPENROUTER_API_KEYS,
    OPENROUTER_MODEL,
)

MAX_SFX_PER_REEL = 6
MIN_SFX_GAP = 2.5


def get_available_sfx() -> List[str]:
    """Get all available sound effect files."""
    sfx_files = []
    
    if not os.path.exists(SOUND_EFFECTS_DIR):
        print(f"Sound effects directory not found: {SOUND_EFFECTS_DIR}")
        return sfx_files
    
    for filename in os.listdir(SOUND_EFFECTS_DIR):
        if filename.lower().endswith((".mp3", ".wav", ".ogg")):
            sfx_files.append(os.path.join(SOUND_EFFECTS_DIR, filename))
    
    print(f"Found {len(sfx_files)} sound effects")
    return sfx_files


def get_sfx_name(filepath: str) -> str:
    """Extract clean name from SFX filepath."""
    basename = os.path.splitext(os.path.basename(filepath))[0]
    return basename.lower().strip()


def classify_sfx_with_llm(
    story_text: str,
    sfx_names: List[str],
) -> List[Dict]:
    """Use LLM to decide which SFX to use and where."""
    sfx_list_str = ", ".join([f'"{name}"' for name in sfx_names])
    
    prompt = f"""You are a TikTok video editor placing sound effects in a story narration.

AVAILABLE SOUND EFFECTS (pick from these EXACT names):
{sfx_list_str}

STORY:
{story_text}

YOUR JOB:
Pick EXACTLY 5 moments where a sound effect would be funny or impactful.
For each moment, tell me:
1. The EXACT word or short phrase from the story where it should trigger
2. Which sound effect to use from the list above

RULES:
- Use each sound effect at most ONCE
- Place SFX at dramatic moments, punchlines, awkward reveals, or shocking parts
- Think like a viral TikTok editor - timing is everything
- Don't cluster them - spread them across the story
- Maximum 5 sound effects total

Return ONLY this JSON array (no other text):
[{{"word": "exact word from story", "sfx": "sound effect name"}}]"""

    _sfx2_key_idx = getattr(_suggest_sfx_placements, '_key_idx', 0)
    for _attempt in range(len(OPENROUTER_API_KEYS)):
        key = OPENROUTER_API_KEYS[_sfx2_key_idx % len(OPENROUTER_API_KEYS)]
        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            if response.status_code == 429:
                _sfx2_key_idx += 1
                time.sleep(2)
                continue
            response.raise_for_status()
            _suggest_sfx_placements._key_idx = _sfx2_key_idx + 1
        
            result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
            if "[" in result and "]" in result:
                start = result.index("[")
                end = result.rindex("]") + 1
                json_str = result[start:end]
                placements = json.loads(json_str)
                
                valid = []
                for p in placements:
                    if "word" in p and "sfx" in p:
                        sfx_name = p["sfx"].lower().strip()
                        matched_sfx = None
                        for available in sfx_names:
                            if sfx_name in available or available in sfx_name:
                                matched_sfx = available
                                break
                        
                        if matched_sfx:
                            valid.append({
                                "word": p["word"],
                                "sfx_name": matched_sfx,
                            })
                
                return valid[:MAX_SFX_PER_REEL]
        
        except (requests.RequestException, json.JSONDecodeError, ValueError):
            _sfx2_key_idx += 1
            time.sleep(2)
            continue
    
    return []


def find_word_timestamp(
    word: str,
    subtitle_entries: List[Dict],
) -> Optional[float]:
    """Find the timestamp where a specific word appears."""
    word_lower = word.lower().strip()
    
    for entry in subtitle_entries:
        text = entry["text"].lower()
        
        if word_lower in text:
            words_in_entry = text.split()
            word_idx = 0
            for i, w in enumerate(words_in_entry):
                if word_lower in w:
                    word_idx = i
                    break
            
            duration = entry["end_time"] - entry["start_time"]
            position = (word_idx / max(len(words_in_entry), 1)) * duration
            return entry["start_time"] + position
    
    for entry in subtitle_entries:
        text = entry["text"].lower()
        words = text.split()
        
        for i, w in enumerate(words):
            if (word_lower in w or w in word_lower or 
                any(p in w for p in word_lower.split() if len(p) > 3)):
                duration = entry["end_time"] - entry["start_time"]
                position = (i / max(len(words), 1)) * duration
                return entry["start_time"] + position
    
    return None


def detect_sfx_triggers(
    story_text: str,
    subtitle_entries: List[Dict],
) -> List[Dict]:
    """Detect SFX trigger points using LLM classification."""
    available_sfx = get_available_sfx()
    
    if not available_sfx:
        print("No sound effects available")
        return []
    
    sfx_names = [get_sfx_name(path) for path in available_sfx]
    sfx_map = {name: path for name, path in zip(sfx_names, available_sfx)}
    
    print(f"Available SFX: {sfx_names}")
    
    placements = classify_sfx_with_llm(story_text, sfx_names)
    
    if not placements:
        print("LLM classification failed, using fallback")
        return fallback_sfx_detection(story_text, subtitle_entries, sfx_map)
    
    print(f"LLM suggested {len(placements)} SFX placements")
    
    triggers = []
    used_sfx = set()
    
    for placement in placements:
        word = placement.get("word", "")
        sfx_name = placement.get("sfx_name", "")
        
        if sfx_name in used_sfx or sfx_name not in sfx_map:
            continue
        
        timestamp = find_word_timestamp(word, subtitle_entries)
        
        if timestamp is None:
            words = word.split()
            for w in words:
                if len(w) > 3:
                    timestamp = find_word_timestamp(w, subtitle_entries)
                    if timestamp is not None:
                        break
        
        if timestamp is not None:
            triggers.append({
                "timestamp": timestamp,
                "sfx_name": sfx_name,
                "sfx_file": sfx_map[sfx_name],
            })
            used_sfx.add(sfx_name)
    
    triggers.sort(key=lambda x: x["timestamp"])
    
    filtered = []
    last_ts = -MIN_SFX_GAP
    
    for trigger in triggers:
        if trigger["timestamp"] - last_ts >= MIN_SFX_GAP:
            filtered.append(trigger)
            last_ts = trigger["timestamp"]
    
    print(f"Final SFX: {len(filtered)} triggers")
    for t in filtered:
        print(f"  {t['timestamp']:.1f}s - {t['sfx_name']}")
    
    return filtered


def fallback_sfx_detection(
    story_text: str,
    subtitle_entries: List[Dict],
    sfx_map: Dict[str, str],
) -> List[Dict]:
    """Fallback SFX detection using keyword matching."""
    trigger_map = {
        "vine boom": ["shock", "disbelief", "what", "seriously", "unbelievable", "omg"],
        "bruh": ["bruh", "fail", "stupid", "dumb", "seriously"],
        "faah": ["fart", "stink", "gross", "disgusting", "smell"],
        "record scratch": ["wait", "hold on", "plot twist", "actually"],
        "sad trumpet": ["sad", "cry", "depressed", "lonely", "heartbroken"],
        "wilhelm scream": ["scream", "fall", "pain", "ouch", "hurt"],
        "metal pipe": ["clang", "hit", "punch", "slap", "metal"],
        "ai horn": ["horn", "honk", "alert", "warning"],
        "confused male voice huh": ["confused", "huh", "what do you mean"],
        "male what": ["what", "really", "seriously"],
        "damage blowhole": ["damage", "destroyed", "obliterated"],
    }
    
    triggers = []
    story_lower = story_text.lower()
    
    for sfx_name, keywords in trigger_map.items():
        sfx_file = None
        for name, path in sfx_map.items():
            if sfx_name in name or name in sfx_name:
                sfx_file = path
                break
        
        if not sfx_file:
            continue
        
        for keyword in keywords:
            if keyword in story_lower:
                timestamp = find_word_timestamp(keyword, subtitle_entries)
                if timestamp is not None:
                    triggers.append({
                        "timestamp": timestamp,
                        "sfx_name": sfx_name,
                        "sfx_file": sfx_file,
                    })
                    break
    
    triggers.sort(key=lambda x: x["timestamp"])
    return triggers[:MAX_SFX_PER_REEL]


def get_sfx_at_timestamp(
    triggers: List[Dict],
    timestamp: float,
    tolerance: float = 0.15,
) -> Optional[str]:
    """Get SFX file to play at a specific timestamp."""
    for trigger in triggers:
        if abs(trigger["timestamp"] - timestamp) < tolerance:
            return trigger["sfx_file"]
    return None
