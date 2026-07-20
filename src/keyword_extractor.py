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
        # Each fallback maps to a unique topic so topic_memory tracks it
        fallbacks = [
            ("getting fired in the most dramatic way possible at work", "Bestie, I deadass got fired over the intercom at my retail job in front of every single customer, and my manager said it was a motivational technique to build character, I literally walked out without my apron."),
            ("dating app horror story where the person turned out to be completely different", "No cap, I went on a date with someone from tinder and they showed up with their mom who started interviewing me about my credit score and retirement plan, and the person just sat there nodding along like this was totally normal."),
            ("my best friend stole my identity and opened credit cards in my name", "So I just found out my best friend of fifteen years has been opening credit cards in my name since high school, and now I owe forty thousand dollars I never spent, and she bought a boat with it."),
            ("coworker who took credit for my work and got promoted instead of me", "My coworker literally copy pasted my entire project into an email to our CEO and got promoted to senior manager while I was on vacation, and when I confronted her she said teamwork means sharing credit."),
            ("caught my neighbor secretly recording everyone in the neighborhood", "I just discovered my neighbor has cameras pointing into every single window on our street and he has been selling the footage online as a reality show called suburban surveillance, and fifty thousand people are subscribed to it."),
            ("roommate who was secretly selling our belongings on ebay", "My roommate has been selling my clothes on ebay while I am at work and he told me it was a laundry service, and I only found out when a stranger showed up at our door wearing my favorite hoodie."),
            ("wild road trip where the car broke down in the middle of nowhere", "So our car broke down in the desert at two in the morning and the only thing for miles was a gas station run by a guy who said he would fix it if we listened to his four hour podcast about conspiracy theories."),
            ("boss who made me work on my birthday and then fired me the next day", "My boss made me work a double shift on my birthday and then fired me the next morning for being too tired to smile at customers, and she gave my parking spot to the intern who started that same day."),
            ("family reunion that ended with the police being called", "Our family reunion turned into a full blown war when my uncle brought a karaoke machine and my aunt started singing songs about their divorce, and now nobody is talking to each other and the police said we cannot have family gatherings over twenty people anymore."),
            ("online shopping addiction that nearly cost me my house", "I just realized I spent forty thousand dollars on things I do not need from online shopping at three in the morning, and my wife found out when the delivery driver brought the twentieth box this week and asked if we were opening a store."),
            ("vacation from hell where every single thing went wrong", "Our dream vacation to hawaii turned into a nightmare when we got food poisoning on the plane, lost our luggage, our hotel caught fire, and the only restaurant that was open gave us the wrong order and charged us double."),
            ("childhood friend who turned out to be living a complete lie", "My childhood best friend told me he was a doctor for ten years and I just found out he works at a fast food restaurant and has been lying to everyone including his own family, and he even had a fake diploma on his wall."),
            ("nightmare HOA president who tried to fine me for everything", "My HOA president fined me five hundred dollars for having the wrong shade of green on my front door and then fined me again for complaining about the fine, and when I went to the meeting she had a PowerPoint presentation about my lawn."),
            ("person I went on a date with who turned out to be married with kids", "I went on a date with someone who told me they were single and then their spouse showed up at the restaurant with their three kids and started screaming at me, and the person just sat there pretending to be a stranger."),
            ("betrayal by someone I considered family for over twenty years", "My brother in law has been embezzling money from our family business for twenty years and when we confronted him he said he was doing us a favor by testing our security systems, and now our parents are not speaking to each other."),
            ("wild story from working the night shift at a hospital", "A patient at the hospital where I work as a night nurse escaped through a window and was found three blocks away trying to teach a raccoon how to do paperwork, and security said this was the third time this month."),
            ("story about accidentally going viral for the most embarrassing reason", "I accidentally went viral for a video of me tripping over my own feet at a job interview and the clip has two million views now and my boss made it the company screensaver, and everyone calls me tripod at work."),
            ("crazy story about a secret room I found in my house after living there for years", "I found a secret room behind my bathroom wall that had a full office setup and someone had been living there without me knowing for months, and when I confronted the person they said they were the previous tenant and forgot to move out."),
            ("strange encounter with a stranger at 3am in a gas station", "At three in the morning a stranger at the gas station handed me a sealed envelope and said open it when you get home, and inside was a letter from my future self warning me about this exact moment, and I am still processing what that means."),
            ("story about a pet that caused absolute destruction worth thousands of dollars", "My dog ate an entire antique table that was worth fifteen thousand dollars and when the appraiser came to assess the damage the dog ate the appraisal paperwork too, and now insurance says they cannot cover an act of dog."),
            ("embarrassing moment at work that went viral on social media", "I accidentally hit reply all to an email calling my entire office a bunch of corporate zombies and it went to our five hundred person company email list, and someone screen recorded it before I could delete it and now it has a million views on tiktok."),
            ("strange addiction that nobody in my life knew about until it blew up", "I had a secret addiction to buying mannequins and I had collected over two hundred of them in my garage and my wife thought I was cheating because I was spending all my money on something, and when she found them she fainted and called the police."),
            ("revenge story where I got back at someone who wronged me spectacularly", "My ex roommate stole three months of rent from me so I replaced every single item in the apartment with a slightly smaller version and he did not notice for six weeks, and when he finally did he called the police but they said it was not technically a crime."),
            ("nightmare HOA president who tried to fine me for everything part two", "My HOA president tried to fine me for having a bird feeder because she said it attracted unauthorized wildlife to the neighborhood, and when I removed it she fined me for decreasing property values by removing curb appeal."),
            ("stranger on a train told me something that changed my life forever", "A complete stranger on the train sat next to me and whispered that I should check the back of my old photo album, and when I got home I found a lottery ticket worth fifty thousand dollars that my grandmother hid there twenty years ago."),
            ("moved into a new apartment and discovered the previous tenant was a hoarder", "I moved into my new apartment and found four hundred old newspapers stacked floor to ceiling in the closet and the landlord said it was a reading nook, and when I tried to throw them out the historical society showed up and said they were evidence."),
            ("teacher in high school who had a secret second family nobody knew about", "My high school teacher had a completely separate family in the next town over and both families showed up to his retirement party thinking they were the only ones, and the school had to hire a therapist for the entire student body."),
            ("neighborhood gossip that destroyed multiple families overnight", "One rumor about a fake affair spread through our entire neighborhood in a single day and three couples got divorced before anyone bothered to check if it was true, and it turned out to be started by a kid who was bored on summer break."),
            ("wild story from working the night shift at a hospital part two", "A patient checked himself out of the hospital at two in the morning and came back an hour later riding a stolen riding mower with a raccoon on his shoulder, and security said they were impressed by his commitment to the bit."),
            ("story about a pet that caused absolute destruction worth thousands of dollars part two", "My cat knocked over a candle that started a small fire that set off the sprinkler system that flooded the entire apartment and ruined my roommate collection of rare vinyl records worth twenty thousand dollars, and the cat just sat there grooming himself."),
        ]

        available = [(topic, s) for topic, s in fallbacks if topic not in used_topics]
        if not available:
            available = fallbacks

        forced_topic, script = random.choice(available)

    script = script.strip().strip('"').strip("'")
    print(f"Generated absurd script ({len(script.split())} words)")

    record_topic(forced_topic, script)
    return script
