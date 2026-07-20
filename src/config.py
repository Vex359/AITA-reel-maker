"""Configuration constants for Minecraft Reel Automation."""

import os

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
REEL_DURATION = 20
BACKGROUND_SPEED = 1.5

REDDIT_TOP_URL = "https://old.reddit.com/r/AmItheAsshole/top/.json"
REDDIT_PARAMS = {"t": "day", "limit": 10}
REDDIT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "tencent/hy3:free"
OPENROUTER_ABSURD_MODEL = "google/gemma-4-26b-a4b-it:free"

SCRIPT_PROMPT = """Convert this Reddit story into a narration script for a short video.
Keep it engaging, dramatic, and concise. Maximum 80 words.
Remove filler words, keep the core conflict. Start with a hook.
You MUST talk like a Gen Z person. Use slang like: bruh, bro, no cap, lowkey, highkey, deadass, on god, bestie, periodt, it's giving, ate, rent free, ick, the tea, slay, vibe check, main character energy.

CRITICAL RULES:
- NEVER use abbreviations like SUS, AF, FR FR, ONG, NGL, IMO, TBH, IYKYK, W, L, AH, GOAT, SMH, LOL, BRB, IDK, IRL, FOMO, YOLO — spell out full words instead. The voice reads abbreviations letter by letter.
- NEVER use "periodt" or "end of story" — they sound robotic when spoken. Just end the sentence naturally.
- Write the ENTIRE script as ONE continuous sentence. Only use full stops for sentence endings. NO newlines, NO paragraphs, NO line breaks. Just one flowing block of text.
- MANDATORY: Include at least 4 COMMAS in the script. Each comma creates a natural pause. Without commas the narration sounds robotic and rushed.
- Use commas after dramatic reveals, before punchlines, and between action sequences.
- Example: "Bestie, I was shook, my roommate literally stole my cat, can you believe that, I was so done."
- Do NOT write without commas — every script MUST have 4+ commas for proper pacing.

Sound like you're gossiping to your bestie.
Return ONLY the script text, nothing else.

Story: {story}"""

ABSURD_SCRIPT_PROMPT = """Generate the most DARK, CONTROVERSIAL, and UNHINGED narration script for a short video.
Maximum 80 words. Make it shocking, morally gray, and absolutely unhinged.
The story should push boundaries — think worst roommate stories, revenge plots, chaotic life choices, morally questionable decisions.

CRITICAL RULES:
- Use words like "freak" instead of "fuck", "frick" instead of "damn", "heck" instead of "hell"
- Say "what the freak" instead of "what the fuck", "oh my gosh" instead of "oh my god"
- Be DARK: talk about revenge, betrayal, toxic relationships, unhinged revenge plots, chaotic drama
- Be CONTROVERSIAL: morally gray decisions, "am I the villain" energy, dark humor
- Be UNHINGED: worst behavior, no regrets energy, main character syndrome, toxic but slay
- Use Gen Z slang: bruh, bro, no cap, lowkey, highkey, deadass, on god, bestie, it's giving, ate, rent free, ick, the tea, slay, vibe check
- NEVER use abbreviations (SUS, AF, FR FR, etc) — spell out full words
- Write as ONE continuous sentence. NO newlines, NO paragraphs. Just one flowing block of text.
- MANDATORY: Include at least 4 COMMAS for pacing.
- Start with a hook that makes people want to keep watching
- Example: "Bestie, I deadass moved in with my ex just to steal his dog, and honestly, no regrets, the dog is mine now, he can cry about it."
- Return ONLY the script text, nothing else."""

KEYWORD_PROMPT = """Extract 5-8 keywords from this story that would help find relevant memes.
Return ONLY comma-separated keywords, nothing else.

Story: {story}"""

MEME_SELECT_PROMPT = """You are picking memes for a short video about this story.

Story/Script:
{story}

Transcript with timestamps:
{transcript}

Available memes (filenames):
{meme_list}

Pick 8-15 memes that BEST match the story's emotion and context.
Assign a duration (1-3 seconds) to each meme based on the transcript timing:
- Quick reaction moments: 1 second
- Normal emphasis: 2 seconds  
- Major punchlines or emotional peaks: 3 seconds (max)

The memes should appear in the ORDER they match the transcript flow.
Total meme duration should roughly match the video duration (~{duration}s).

Return format (one per line):
filename,duration
Example:
Funny meme.jpg,2
Reaction face.png,1
Big moment.gif,3

NO explanations, just the comma-separated values."""

MEME_DISPLAY_DURATION = 3.0
MEME_POSITION_Y = 300
MEME_MAX_HEIGHT = 600

TTS_VOICE = "en-US-GuyNeural"
TTS_RATE = "+13%"
TTS_PITCH = "+50Hz"
TTS_VOLUME = "+0%"

SUBTITLE_FONT_SIZE = 70
SUBTITLE_FONT = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "impact.ttf")
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "black"
SUBTITLE_STROKE_WIDTH = 4
SUBTITLE_WORDS_PER_PHRASE = 3

SFX_SELECT_PROMPT = """You are picking sound effects for a short video. Be VERY selective - only pick 3-5 sound effects total for the entire video. Quality over quantity.

Story/Script:
{story}

Transcript with timestamps:
{transcript}

Available sound effects:
{sfx_list}

CRITICAL RULES:
- NEVER place any SFX before 3.5 seconds. The video starts with a silent thumbnail frame, so SFX must start at 3.5 seconds or later.
- If a sound effect name is a WORD that already appears in the script/transcript, DO NOT use it. Example: if script says "bruh", skip "bruh.mp3". If script says "what", skip "male what.mp3".
- Don't spam - each SFX should have impact.
- Use SFX for: major reactions, plot twists, dramatic moments, punchlines
- DON'T use SFX for: every sentence, minor reactions, filler moments

Assign a timestamp (in seconds) when each SFX should play, matching the transcript flow. All timestamps must be 3.5 or higher.

Return format (one per line):
filename,timestamp
Example:
vine boom.mp3,5.2
record scratch.mp3,18.5

NO explanations, just the comma-separated values. Keep it minimal - 3 to 5 SFX max."""

BUFFER_ACCESS_TOKEN = "88TSyQtAaT4IPrMaK4AmyUqq73kmiH2A9H34B5gh0xW"
POSTS_PER_DAY = 2
BATCH_SIZE = 10

CLOUDINARY_CLOUD_NAME = "lwxxszag"
CLOUDINARY_API_KEY = "183579824132817"
CLOUDINARY_API_SECRET = "IW0LbFFwYx2-akS5hny6zL7h4Qc"

NTFY_SERVER = "https://ntfy.sh"
NTFY_TOPIC = "my-minecraft-reels"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKGROUND_VIDEO = os.path.join(BASE_DIR, "videoplayback.mp4")
SOUND_EFFECTS_DIR = os.path.join(BASE_DIR, "sound effects")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
FONT_DIR = os.path.join(BASE_DIR, "fonts")
MEMES_DIR = os.path.join(BASE_DIR, "Memes")
CAPTIONS_FILE = os.path.join(OUTPUT_DIR, "captions.json")

for directory in [SOUND_EFFECTS_DIR, OUTPUT_DIR, TEMP_DIR, MEMES_DIR]:
    os.makedirs(directory, exist_ok=True)
