"""Keyword extraction and script generation using OpenRouter free models."""

import requests
from typing import List

from .config import (
    OPENROUTER_API_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    SCRIPT_PROMPT,
    KEYWORD_PROMPT,
)


def call_llm(prompt: str) -> str:
    """Call OpenRouter API with a prompt."""
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
            },
            timeout=60,
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
    except Exception as e:
        print(f"LLM API error: {e}")
        return ""


def generate_script(story_text: str) -> str:
    """Convert a Reddit story into a 20-second narration script."""
    prompt = SCRIPT_PROMPT.format(story=story_text)
    script = call_llm(prompt)
    
    if not script:
        words = story_text.split()
        script = " ".join(words[:75]) + "..."
    
    script = script.strip().strip('"').strip("'")
    print(f"Generated script ({len(script.split())} words)")
    return script


def extract_keywords(story_text: str) -> List[str]:
    """Extract meme-relevant keywords from a story."""
    prompt = KEYWORD_PROMPT.format(story=story_text)
    response = call_llm(prompt)
    
    if not response:
        return ["funny", "drama", "relationship", "family", "conflict"]
    
    keywords = [kw.strip().strip('"').strip("'") for kw in response.split(",")]
    keywords = [kw for kw in keywords if kw and len(kw) > 1][:8]
    
    if not keywords:
        keywords = ["funny", "drama", "relationship", "family", "conflict"]
    
    return keywords
