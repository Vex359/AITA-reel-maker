"""Local meme fetcher using curated meme folders with LLM-powered selection."""

import os
import random
import shutil
import requests
from typing import List, Optional

from .config import (
    MEMES_DIR,
    TEMP_DIR,
    MEME_SELECT_PROMPT,
    SFX_SELECT_PROMPT,
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    OPENROUTER_MODEL,
    SOUND_EFFECTS_DIR,
)

# Map emotional keywords to meme folder categories
KEYWORD_TO_CATEGORY = {
    # Angry/Wicked
    "angry": "Angry - Wicked",
    "mad": "Angry - Wicked",
    "rage": "Angry - Wicked",
    "wicked": "Angry - Wicked",
    "evil": "Angry - Wicked",
    
    # Dumb - Genius
    "dumb": "Dumb - Genius",
    "stupid": "Dumb - Genius",
    "smart": "Dumb - Genius",
    "genius": "Dumb - Genius",
    "idiot": "Dumb - Genius",
    "clever": "Dumb - Genius",
    
    # Funny - Not funny
    "funny": "Funny - Not funny",
    "laugh": "Funny - Not funny",
    "humor": "Funny - Not funny",
    "comedy": "Funny - Not funny",
    "clown": "Funny - Not funny",
    "joke": "Funny - Not funny",
    "lol": "Funny - Not funny",
    "haha": "Funny - Not funny",
    
    # Horny
    "horny": "Horny",
    "love": "Horny",
    "romance": "Horny",
    
    # Humm - Not interesting - Boring
    "boring": "Humm - Not interesting - Boring",
    "meh": "Humm - Not interesting - Boring",
    "whatever": "Humm - Not interesting - Boring",
    "uninterested": "Humm - Not interesting - Boring",
    
    # Offend
    "offend": "Offend",
    "insult": "Offend",
    "disrespect": "Offend",
    "attack": "Offend",
    
    # Sad - Oof - Lose
    "sad": "Sad - Oof - Lose",
    "cry": "Sad - Oof - Lose",
    "depressed": "Sad - Oof - Lose",
    "lose": "Sad - Oof - Lose",
    "fail": "Sad - Oof - Lose",
    "oof": "Sad - Oof - Lose",
    
    # Sweat - Run away
    "sweat": "Sweat - Run away",
    "nervous": "Sweat - Run away",
    "scared": "Sweat - Run away",
    "afraid": "Sweat - Run away",
    "run": "Sweat - Run away",
    "panic": "Sweat - Run away",
    
    # WTF
    "wtf": "WTF",
    "confused": "WTF",
    "what": "WTF",
    "huh": "WTF",
    "weird": "WTF",
    "strange": "WTF",
    "bizarre": "WTF",
    
    # Yes - Win - Love
    "yes": "Yes - Win - Love",
    "win": "Yes - Win - Love",
    "success": "Yes - Win - Love",
    "victory": "Yes - Win - Love",
    "good": "Yes - Win - Love",
    "happy": "Yes - Win - Love",
    "excited": "Yes - Win - Love",
    "celebrate": "Yes - Win - Love",
}


def get_all_meme_categories() -> List[str]:
    """Get list of all meme category folders."""
    if not os.path.exists(MEMES_DIR):
        print(f"Memes directory not found: {MEMES_DIR}")
        return []
    
    categories = []
    for item in os.listdir(MEMES_DIR):
        if os.path.isdir(os.path.join(MEMES_DIR, item)):
            categories.append(item)
    
    return categories


def get_memes_in_category(category: str) -> List[str]:
    """Get all meme files in a category folder."""
    category_path = os.path.join(MEMES_DIR, category)
    if not os.path.exists(category_path):
        return []
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    memes = []
    
    for file in os.listdir(category_path):
        if os.path.splitext(file)[1].lower() in valid_extensions:
            memes.append(os.path.join(category_path, file))
    
    return memes


def get_category_for_keyword(keyword: str) -> Optional[str]:
    """Map a keyword to a meme category."""
    keyword_lower = keyword.lower()
    
    # Direct match
    if keyword_lower in KEYWORD_TO_CATEGORY:
        return KEYWORD_TO_CATEGORY[keyword_lower]
    
    # Partial match
    for key, category in KEYWORD_TO_CATEGORY.items():
        if key in keyword_lower or keyword_lower in key:
            return category
    
    return None


def select_memes_from_categories(
    categories: List[str],
    count: int,
    used_memes: set = None
) -> List[str]:
    """Randomly select memes from given categories."""
    if used_memes is None:
        used_memes = set()
    
    selected = []
    
    # Collect all available memes from categories
    available_memes = []
    for category in categories:
        memes = get_memes_in_category(category)
        for meme in memes:
            if meme not in used_memes:
                available_memes.append(meme)
    
    # If not enough unique memes, allow repeats
    if len(available_memes) < count:
        available_memes = []
        for category in categories:
            memes = get_memes_in_category(category)
            available_memes.extend(memes)
    
    # Randomly select
    if available_memes:
        selected = random.sample(available_memes, min(count, len(available_memes)))
    
    return selected


def copy_meme_to_temp(meme_path: str, index: int) -> Optional[str]:
    """Copy a meme to the temp directory with a unique name."""
    try:
        ext = os.path.splitext(meme_path)[1].lower()
        dest_path = os.path.join(TEMP_DIR, f"meme_{index:03d}{ext}")
        
        shutil.copy2(meme_path, dest_path)
        print(f"Copied meme: {index:03d} -> {dest_path}")
        return dest_path
        
    except Exception as e:
        print(f"Error copying meme {index}: {e}")
        return None


def select_memes_with_llm(script: str, candidate_memes: List[str], count: int = 8, 
                          transcript: str = "", duration: float = 20.0) -> List[tuple]:
    """Use LLM to select memes with variable durations based on transcript.
    
    Args:
        script: The video script/narration text
        candidate_memes: List of full paths to candidate meme files
        count: Number of memes to select
        transcript: Transcript with timestamps for timing context
        duration: Total video duration in seconds
        
    Returns:
        List of tuples: (meme_path, duration_seconds)
    """
    meme_filenames = [os.path.basename(m) for m in candidate_memes]
    meme_list_str = "\n".join([f"- {fn}" for fn in meme_filenames])
    
    # Build transcript string if provided
    transcript_str = ""
    if transcript:
        for entry in transcript:
            start = entry.get('start_time', 0)
            text = entry.get('text', '')
            transcript_str += f"[{start:.1f}s] {text}\n"
    else:
        transcript_str = "No transcript available - use story context only."
    
    prompt = MEME_SELECT_PROMPT.format(
        story=script, 
        meme_list=meme_list_str,
        transcript=transcript_str,
        duration=int(duration)
    )
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
            },
            timeout=15,
        )
        response.raise_for_status()
        
        content = response.json()["choices"][0]["message"]["content"].strip()
        print(f"LLM meme selection:\n{content[:200]}...")
        
        # Parse the new format: filename,duration
        selected_memes = []
        for line in content.split("\n"):
            line = line.strip()
            if not line or "," not in line:
                continue
            
            parts = line.split(",", 1)
            filename = parts[0].strip()
            try:
                meme_duration = float(parts[1].strip())
                meme_duration = max(1.0, min(3.0, meme_duration))  # Clamp to 1-3 seconds
            except (ValueError, IndexError):
                meme_duration = 2.0  # Default to 2 seconds
            
            # Find matching meme path
            for meme_path in candidate_memes:
                if os.path.basename(meme_path).lower() == filename.lower():
                    selected_memes.append((meme_path, meme_duration))
                    break
            
            if len(selected_memes) >= count:
                break
        
        # If LLM didn't return enough, fill with random
        if len(selected_memes) < count:
            used_paths = [m[0] for m in selected_memes]
            remaining = [m for m in candidate_memes if m not in used_paths]
            extra_count = min(count - len(selected_memes), len(remaining))
            if extra_count > 0:
                extra = random.sample(remaining, extra_count)
                for meme_path in extra:
                    selected_memes.append((meme_path, 2.0))  # Default 2 seconds
        
        return selected_memes[:count]
        
    except Exception as e:
        print(f"LLM selection failed, falling back to random: {e}")
        selected = random.sample(candidate_memes, min(count, len(candidate_memes)))
        return [(m, 2.0) for m in selected]  # Default 2 seconds each


def fetch_and_download_memes(keywords: List[str], count: int = 20, script: str = "",
                             subtitles: List[dict] = None) -> List[tuple]:
    """Fetch memes from local folders based on keywords, using LLM for smart selection.
    
    Args:
        keywords: List of keywords to match meme categories
        count: Number of memes to fetch
        script: The video script for LLM-based meme selection
        subtitles: List of subtitle entries with timing info
        
    Returns:
        List of tuples: (meme_path, duration_seconds)
    """
    print("Fetching memes from local folder...")
    
    all_categories = get_all_meme_categories()
    if not all_categories:
        print("No meme categories found!")
        return []
    
    print(f"Available categories: {len(all_categories)}")
    
    matched_categories = set()
    for keyword in keywords:
        category = get_category_for_keyword(keyword)
        if category:
            matched_categories.add(category)
            print(f"  Keyword '{keyword}' -> Category: {category}")
    
    if not matched_categories:
        print("No keyword matches, using random categories")
        num_random = min(3, len(all_categories))
        matched_categories = set(random.sample(all_categories, num_random))
    
    print(f"Using categories: {matched_categories}")
    
    candidate_memes = []
    for category in matched_categories:
        memes = get_memes_in_category(category)
        candidate_memes.extend(memes)
    
    if len(candidate_memes) < count:
        other_categories = [c for c in all_categories if c not in matched_categories]
        for category in other_categories:
            memes = get_memes_in_category(category)
            candidate_memes.extend(memes)
            if len(candidate_memes) >= count * 3:
                break
    
    candidate_memes = list(set(candidate_memes))
    print(f"Candidate memes: {len(candidate_memes)}")
    
    # Calculate total duration from subtitles
    total_duration = 20.0
    if subtitles:
        total_duration = max(s.get('end_time', 0) for s in subtitles)
    
    if script:
        selected_memes = select_memes_with_llm(
            script, candidate_memes, count=count,
            transcript=subtitles or [], duration=total_duration
        )
    else:
        selected_memes = random.sample(candidate_memes, min(count, len(candidate_memes)))
        selected_memes = [(m, 2.0) for m in selected_memes]
    
    copied_memes = []
    for i, (meme_path, meme_duration) in enumerate(selected_memes):
        dest_path = copy_meme_to_temp(meme_path, i)
        if dest_path:
            copied_memes.append((dest_path, meme_duration))
    
    print(f"Prepared {len(copied_memes)} memes")
    return copied_memes


def get_available_sfx() -> List[str]:
    """Get list of available sound effects."""
    if not os.path.exists(SOUND_EFFECTS_DIR):
        return []
    
    valid_extensions = {'.mp3', '.wav', '.ogg', '.m4a'}
    sfx_files = []
    
    for file in os.listdir(SOUND_EFFECTS_DIR):
        if os.path.splitext(file)[1].lower() in valid_extensions:
            sfx_files.append(file)
    
    return sfx_files


def select_sfx_with_llm(script: str, transcript: List[dict], duration: float) -> List[tuple]:
    """Use LLM to select sound effects with precise timing.
    
    Returns:
        List of tuples: (filename, timestamp_seconds)
    """
    available_sfx = get_available_sfx()
    if not available_sfx:
        print("No sound effects found!")
        return []
    
    sfx_list_str = "\n".join([f"- {sfx}" for sfx in available_sfx])
    
    transcript_str = ""
    if transcript:
        for entry in transcript:
            start = entry.get('start_time', 0)
            text = entry.get('text', '')
            transcript_str += f"[{start:.1f}s] {text}\n"
    else:
        transcript_str = "No transcript available."
    
    prompt = SFX_SELECT_PROMPT.format(
        story=script,
        transcript=transcript_str,
        sfx_list=sfx_list_str,
    )
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
            },
            timeout=15,
        )
        response.raise_for_status()
        
        content = response.json()["choices"][0]["message"]["content"].strip()
        print(f"LLM SFX selection:\n{content[:200]}...")
        
        selected_sfx = []
        for line in content.split("\n"):
            line = line.strip()
            if not line or "," not in line:
                continue
            
            parts = line.split(",", 1)
            filename = parts[0].strip()
            try:
                timestamp = float(parts[1].strip())
                timestamp = max(0.0, min(duration, timestamp))
            except (ValueError, IndexError):
                continue
            
            if filename in available_sfx:
                selected_sfx.append((filename, timestamp))
        
        print(f"Selected {len(selected_sfx)} sound effects")
        return selected_sfx
        
    except Exception as e:
        print(f"LLM SFX selection failed: {e}")
        return []
