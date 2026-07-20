"""Keyword extraction and script generation using OpenRouter free models."""

import os
import json
import requests
from typing import List

from .config import (
    OPENROUTER_API_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_ABSURD_MODEL,
    SCRIPT_PROMPT,
    ABSURD_SCRIPT_PROMPT,
    KEYWORD_PROMPT,
    BASE_DIR,
)

TOPIC_MEMORY_FILE = os.path.join(BASE_DIR, "topic_memory.json")


def load_topic_memory() -> dict:
    if os.path.exists(TOPIC_MEMORY_FILE):
        with open(TOPIC_MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"used_topics": [], "used_scripts": []}


def save_topic_memory(memory: dict):
    with open(TOPIC_MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def record_topic(topic: str, script: str):
    memory = load_topic_memory()
    if topic and topic not in memory["used_topics"]:
        memory["used_topics"].append(topic)
    short_script = script[:200]
    if short_script not in memory["used_scripts"]:
        memory["used_scripts"].append(short_script)
    if len(memory["used_scripts"]) > 50:
        memory["used_scripts"] = memory["used_scripts"][-50:]
    save_topic_memory(memory)


def call_llm(prompt: str, model: str = None) -> str:
    """Call OpenRouter API with a prompt."""
    if model is None:
        model = OPENROUTER_MODEL
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
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


def generate_absurd_script(topic: str = "") -> str:
    import random
    memory = load_topic_memory()
    used_topics = memory.get("used_topics", [])
    used_scripts = memory.get("used_scripts", [])

    avoid_block = ""
    if used_topics:
        avoid_block += "\n\nALREADY COVERED TOPICS (DO NOT repeat these or similar themes):\n"
        for t in used_topics[-30:]:
            avoid_block += f"- {t}\n"
    if used_scripts:
        avoid_block += "\nALREADY USED SCRIPTS (DO NOT copy these phrases or structures):\n"
        for s in used_scripts[-15:]:
            avoid_block += f'- "{s}..."\n'

    diverse_topics = [
        "getting fired in the most dramatic way possible at work",
        "dating app horror story where the person turned out to be completely different",
        "stranger on a train told me something that changed my life forever",
        "my best friend stole my identity and opened credit cards in my name",
        "wild road trip where the car broke down in the middle of nowhere",
        "caught my neighbor secretly recording everyone in the neighborhood",
        "family reunion that ended with the police being called",
        "unhinged customer at my retail job refused to leave the store",
        "moved into a new apartment and discovered the previous tenant was a hoarder",
        "accidentally sent a mean text about my boss to my boss instead of my friend",
        "teacher in high school who had a secret second family nobody knew about",
        "roommate who was secretly selling our belongings on ebay",
        "online shopping addiction that nearly cost me my house",
        "got scammed by someone I trusted completely and lost everything",
        "vacation from hell where every single thing went wrong",
        "coworker who took credit for my work and got promoted instead of me",
        "strange encounter with a stranger at 3am in a gas station",
        "childhood friend who turned out to be living a complete lie",
        "nightmare HOA president who tried to fine me for everything",
        "boss who made me work on my birthday and then fired me the next day",
        "person I went on a date with who turned out to be married with kids",
        "neighborhood gossip that destroyed multiple families overnight",
        "revenge story where I got back at someone who wronged me spectacularly",
        "story about a pet that caused absolute destruction worth thousands of dollars",
        "embarrassing moment at work that went viral on social media",
        "strange addiction that nobody in my life knew about until it blew up",
        "betrayal by someone I considered family for over twenty years",
        "wild story from working the night shift at a hospital",
        "story about accidentally going viral for the most embarrassing reason",
        "crazy story about a secret room I found in my house after living there for years",
    ]

    available = [t for t in diverse_topics if t not in used_topics]
    if not available:
        available = diverse_topics

    forced_topic = random.choice(available)

    prompt = (
        f"You MUST write a narration script about EXACTLY this topic:\n"
        f"\"{forced_topic}\"\n\n"
        f"Do NOT write about any other topic. Stay completely on this topic.{avoid_block}\n\n"
        f"{ABSURD_SCRIPT_PROMPT}"
    )

    script = call_llm(prompt, model=OPENROUTER_ABSURD_MODEL)

    if not script:
        fallbacks = [
            "Bestie, I deadass caught my roommate selling all my furniture while I was at work, and when I confronted him he said the couch looked better on facebook marketplace than in our living room, I was literally speechless.",
            "No cap, I went on a date last week and the person showed up with their entire family including grandparents, and they all started interviewing me like it was a job interview for being their child in law.",
            "So I just found out my neighbor has been stealing my wifi for three years and charging OTHER neighbors for access to it, and honestly I am not even mad I am impressed by the hustle.",
            "My boss literally asked me to work on my birthday and when I said no she put me on a performance improvement plan the next morning, the audacity is actually insane.",
            "I accidentally sent a text calling my roommate a freeloader to the group chat WITH my roommate in it, and now I am sleeping on the couch at my friend place because my roommate changed the locks.",
        ]
        script = random.choice(fallbacks)

    script = script.strip().strip('"').strip("'")
    print(f"Generated absurd script ({len(script.split())} words)")

    record_topic(forced_topic, script)
    return script
