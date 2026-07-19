"""Reddit story scraper for r/AmItheAsshole."""

import random
import requests
from typing import Optional

from .config import (
    REDDIT_TOP_URL,
    REDDIT_PARAMS,
    REDDIT_USER_AGENT,
    REEL_DURATION,
)

FALLBACK_STORIES = [
    {
        "title": "AITA for refusing to pay for my sister's wedding?",
        "body": "My sister is getting married next month and asked me to cover the catering costs, which are about fifteen thousand dollars. She said since I make good money, I should help out family. I told her I'd happily give her a two thousand dollar gift but fifteen thousand is way too much. She called me selfish and said I'm ruining her special day. Our parents are taking her side and saying I should support family. I feel guilty but this seems unreasonable. AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "AITA for telling my roommate his girlfriend can't live here rent free?",
        "body": "My roommate started spending every night with his girlfriend. She's basically moved in without being on the lease. She uses our groceries, takes long showers, and never contributes to utilities. I asked my roommate to either have her pay a third of rent and bills or start staying at her own place. He said I'm being cold hearted and that she's going through a rough time. I get that but I didn't sign up to support a third person. AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "AITA for not inviting my mom to my graduation?",
        "body": "My mom and I have had a complicated relationship since she remarried. She consistently prioritizes my stepdad and his kids over me. When I got into college she didn't help with anything, not even a congratulations. Now I'm graduating and honestly don't want her there. She found out and is devastated. My dad says I should forgive her but I'm still hurt. AITA for not inviting her?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "AITA for refusing to babysit my nieces for free?",
        "body": "My sister has three kids under ten and keeps dropping them off at my place every weekend without asking. Last Saturday she showed up at seven AM and left them until nine PM. When I told her I need notice and can't do this every week she got angry. She said family helps family and I'm being selfish. She's a single mom but that's not my responsibility. AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "My coworker ate my lunch and I reported him to HR",
        "body": "I meal prep every Sunday and bring the same container to work. For the past three weeks my lunch has been disappearing from the fridge. Last Friday I set up my phone to record the fridge area. Sure enough my coworker Steve grabbed my container, ate the whole thing, and threw it away. I showed the video to HR and now Steve is suspended. Everyone says I went too far over a lunch but this has been happening for weeks. AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I refused to give up my plane seat for a family",
        "body": "I paid extra to select my window seat three months in advance. When I boarded a mom asked me to switch so her kid could sit next to the dad. I said no because I specifically chose this seat. She made a scene and other passengers glared at me. The flight attendant said I was within my rights but I still feel bad. The kid was only about six years old. AITA for not giving up my seat?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I told my best friend his girlfriend is cheating",
        "body": "I saw my best friend's girlfriend at a bar with another guy. They were being very flirtatious and at one point she was sitting on his lap. I took a photo and showed my friend. He confronted her and she admitted to emotional cheating. They broke up and now all our friends are blaming me for ruining their relationship. They say it wasn't my place to get involved. Was I wrong to tell him?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I sold my late grandmother's heirloom to pay for college",
        "body": "My grandmother passed away last year and left me her vintage diamond necklace. It's worth about twenty thousand dollars. I'm drowning in student loans and can barely afford rent. My mom says the necklace should stay in the family and that I'm being selfish selling it. She called me heartless for trading grandma's memory for money. I need this degree to have a future though. AITA for selling it?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I told my sister her wedding budget is insane",
        "body": "My sister wants a destination wedding in Italy and asked me to be her maid of honor. The problem is she expects me to pay half of everything. The total budget is forty thousand dollars. I told her I can contribute five thousand max. She started crying and said I'm ruining her dream wedding. Our mom says I should take out a loan for her. I'm a college student with no savings. AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I won't let my brother move in after he kicked me out",
        "body": "Three years ago my brother kicked me out of his apartment when I lost my job. I was homeless for two months. Now he lost his job and wants to crash at my place. I said no. He's begging and our parents are calling me heartless. But I remember sleeping in my car while he posted party pics on Instagram. Why should I help someone who didn't help me? AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I exposed my friend's fake charity on social media",
        "body": "My friend started a GoFundMe claiming to help homeless people. She raised eight thousand dollars. When I asked for proof of donations she got defensive. I found out she spent the money on a vacation. I posted screenshots of our conversation on Twitter. Now she's being sued and her family is threatening me. Was I wrong for exposing her?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I refuse to split my inheritance with my step siblings",
        "body": "My dad passed away and left me his house and savings. My stepmom says I should split it equally with her two kids who aren't even my dad's biological children. The will clearly states everything goes to me. She called me greedy and said dad would have wanted it shared. But he made his wishes clear in legal documents. AITA for keeping what's mine?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I fired my personal trainer for flirting with me",
        "body": "I hired a personal trainer to get in shape. After a month he started texting me outside of gym hours. First it was motivational messages then it turned into asking me out. I told him I wasn't interested. He kept pushing so I reported him to the gym and got a refund. Now he's leaving bad reviews on my business page saying I led him on. AITA for reporting him?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I told my wife her cooking is terrible",
        "body": "My wife has been experimenting with new recipes for months. Every single meal has been burnt or underseasoned. I've been pretending to like it but last night I finally snapped and told her the truth. She hasn't spoken to me since. She's an amazing person but the food is genuinely bad. Should I have kept lying to protect her feelings?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I reported my neighbor's tree that's destroying my fence",
        "body": "My neighbor has a massive oak tree that's been growing into my property for years. Its roots have cracked my fence and are threatening my foundation. I asked him to trim it but he refused. I called the city and they're forcing him to remove part of it. He's furious and says I should have worked it out privately. But I tried for two years. AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I refused to be a surrogate for my sister",
        "body": "My sister can't carry a pregnancy due to medical reasons. She asked me to be her surrogate. I love her but I don't want to go through pregnancy again. I already have three kids and my body hasn't fully recovered. She said I'm being selfish and denying her the chance to be a mom. Our whole family is pressuring me. AITA for saying no?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I told my kids their grandma isn't real",
        "body": "My mother-in-law passed away before my kids were born. My husband has been telling them stories about her and even set up a fake Facebook account pretending to be her. I found out and told my kids the truth. They're devastated and my husband says I destroyed their happiness. But I don't want them built on lies. AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I took back my engagement ring after catching my fiance cheating",
        "body": "I proposed to my girlfriend six months ago with my grandmother's diamond ring. Last week I found explicit messages on her phone with her coworker. I took the ring back immediately. She's begging for another chance and says it was just flirting. Our families are divided. My mom says I should forgive her. But once a cheater always a cheater right? AITA?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I reported my professor for favoritism",
        "body": "My professor consistently gives better grades to students he personally likes. I have proof showing identical answers with different grades. I reported him to the dean. Now he's failing me in his class and says I'm a troublemaker. Other students are afraid to speak up. Was I wrong for standing up against unfair grading?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "I sold my kids college fund to pay for my dream vacation",
        "body": "I've been working nonstop for fifteen years. I saved up eighty thousand dollars in my kids college fund. Last month I took half of it to travel through Europe. My wife is furious and says I stole from our children. But they're only eight and ten years old. I have time to save again. I deserved this break. AITA for using the money?",
        "url": "https://reddit.com/r/AmItheAsshole",
    },
    {
        "title": "Entitled mom demands I give her kid my Switch at the airport",
        "body": "I was waiting for my flight and playing my Nintendo Switch. This woman walks up with her kid and says my kid wants to play with your Switch. I said no sorry I'm using it. She said but he's bored can you just let him hold it. I said no again. She then tried to grab it out of my hands. I pulled away and she called me selfish. Her kid started screaming. Other passengers told me to just let the kid play. I said it costs three hundred dollars I'm not handing it to a stranger. The mom called me every name in the book.",
        "url": "https://reddit.com/r/entitledparents",
    },
    {
        "title": "My entitled sister tried to take my house after my wedding",
        "body": "My sister showed up to my wedding uninvited with her whole family. During the reception she announced to everyone that since I'm single she expects to move into my house rent free. I told her absolutely not. She started crying and said family helps family. My parents backed her up and said I have a spare room so why not. I said because I don't want to live with someone who insults my cooking and trash talks my decorating every day. Now the whole family is calling me heartless.",
        "url": "https://reddit.com/r/entitledparents",
    },
    {
        "title": "Nice guy at work won't take no for an answer",
        "body": "There's this guy at work who keeps asking me out. I've told him no at least ten times. He keeps saying but I'm such a nice guy why won't you give me a chance. Last week he left flowers on my desk with a note saying your loss if you don't date me. I showed it to HR. Now he's saying I'm ruining his career over nothing. He told everyone I led him on by being friendly. Being polite at work does not mean I want to date you.",
        "url": "https://reddit.com/r/niceguys",
    },
    {
        "title": "My mom gave away my cat because she wanted a grandchild instead",
        "body": "I came home from work and my cat was gone. My mom had been visiting and she gave my cat to the neighbor because and I quote she said having a cat is like practice for having a baby and I need to focus on giving her grandkids. I told her she had no right to give away my pet. She said she did me a favor because now I'll have time to find a husband. I'm twenty six and single and happy. She doesn't get to decide what I need. I kicked her out and haven't spoken to her in two weeks.",
        "url": "https://reddit.com/r/entitledparents",
    },
]


def fetch_aita_story() -> dict:
    """Fetch a random top AITA story from Reddit."""
    headers = {
        "User-Agent": REDDIT_USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    try:
        response = requests.get(
            REDDIT_TOP_URL,
            params=REDDIT_PARAMS,
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        
        data = response.json()
        posts = data.get("data", {}).get("children", [])
        
        if not posts:
            return random.choice(FALLBACK_STORIES)
        
        # Filter for text-heavy posts
        good_posts = []
        for post in posts:
            post_data = post.get("data", {})
            selftext = post_data.get("selftext", "")
            title = post_data.get("title", "")
            
            # Prefer posts with substantial text
            if len(selftext) > 150:
                good_posts.append({
                    "title": title,
                    "body": selftext,
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                })
        
        if not good_posts:
            for post in posts:
                post_data = post.get("data", {})
                selftext = post_data.get("selftext", "")
                if selftext:
                    good_posts.append({
                        "title": post_data.get("title", ""),
                        "body": selftext,
                        "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    })
        
        if good_posts:
            return random.choice(good_posts)
        
        return random.choice(FALLBACK_STORIES)
        
    except requests.RequestException:
        return random.choice(FALLBACK_STORIES)


def truncate_story(story: dict, max_words: int = 80) -> dict:
    """Truncate story body to fit narration time.
    
    Args:
        story: dict with title and body
        max_words: maximum words for ~20s narration
        
    Returns:
        Modified story dict with truncated body
    """
    words = story["body"].split()
    
    if len(words) <= max_words:
        return story
    
    # Truncate at sentence boundary if possible
    truncated = " ".join(words[:max_words])
    last_period = truncated.rfind(".")
    
    if last_period > len(truncated) * 0.5:  # At least 50% of truncated
        truncated = truncated[: last_period + 1]
    else:
        truncated += "..."
    
    story["body"] = truncated
    return story
