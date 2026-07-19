"""Test GuyNeural smoothing variations."""
import asyncio
import edge_tts
import os

TEXT = "Bruh no cap this is deadass the most sus thing ever. On god bestie you did NOT just say that. That is lowkey cringe fr fr periodt."
VOICE = "en-US-GuyNeural"
os.makedirs("temp", exist_ok=True)

VARIATIONS = [
    ("guy_pitch30_rate30", "+30Hz", "+30%"),
    ("guy_pitch40_rate25", "+40Hz", "+25%"),
    ("guy_pitch35_rate20", "+35Hz", "+20%"),
    ("guy_pitch25_rate30", "+25Hz", "+30%"),
    ("guy_pitch50_rate20", "+50Hz", "+20%"),
    ("guy_pitch40_rate30", "+40Hz", "+30%"),
]

async def test_voice(name, pitch, rate):
    communicate = edge_tts.Communicate(TEXT, VOICE, rate=rate, pitch=pitch)
    out_path = os.path.join("temp", f"{name}.mp3")
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
    print(f"  Saved: {out_path}")

async def main():
    for name, pitch, rate in VARIATIONS:
        print(f"\nTesting: {name} (pitch={pitch}, rate={rate})")
        await test_voice(name, pitch, rate)
    print("\nDone! Check temp/ folder.")

asyncio.run(main())
