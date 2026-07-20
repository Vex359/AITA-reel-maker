"""Batch reel generation + Buffer scheduling. Run directly or via run_cycle.bat."""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import OUTPUT_DIR, BATCH_SIZE, POSTS_PER_DAY, CAPTIONS_FILE
from src.main import generate_absurd_reel, cleanup_temp
from src.buffer_scheduler import (
    get_instagram_channel, 
    generate_schedule_times, 
    schedule_batch
)
from src.phone_notify import send_reel_ready_notification, send_reminder_notification
from src.reddit_scraper import fetch_aita_story, truncate_story
from src.keyword_extractor import generate_script, generate_absurd_script


def generate_captions(script: str, hook_text: str) -> Dict[str, str]:
    first_sentence = script.split('.')[0].strip()
    if len(first_sentence) > 150:
        first_sentence = first_sentence[:147] + "..."
    
    hashtags = [
        "#minecraftparkour",
        "#aitastories",
        "#redditstories",
        "#parkour",
        "#minecraft",
        "#shorts",
        "#viral",
        "#fyp",
        "#storytime",
        "#drama",
        "#amitheasshole",
        "#reels",
    ]
    
    selected_tags = random.sample(hashtags, min(8, len(hashtags)))
    
    caption = f"{first_sentence}\n\n"
    caption += " ".join(selected_tags)
    caption += "\n\n🔔 Follow for daily stories!"
    
    return {
        "caption": caption,
        "hook": hook_text,
    }


def generate_batch(num_reels: int = BATCH_SIZE) -> List[Dict]:
    print("\n" + "=" * 60)
    print(f"  BATCH GENERATION: {num_reels} REELS")
    print("=" * 60)
    
    results = []
    
    for i in range(num_reels):
        print(f"\n{'─' * 40}")
        print(f"  REEL {i + 1} of {num_reels}")
        print(f"{'─' * 40}")
        
        try:
            video_path = generate_absurd_reel()
            hook_text = os.path.splitext(os.path.basename(video_path))[0]
            caption_data = generate_captions("", hook_text)
            
            results.append({
                "video_path": video_path,
                "caption": caption_data["caption"],
                "hook": hook_text,
                "generated_at": datetime.now().isoformat(),
            })
            
            print(f"\n  ✓ Reel {i + 1} generated: {os.path.basename(video_path)}")
            cleanup_temp()
            
        except Exception as e:
            print(f"\n  ✗ Reel {i + 1} failed: {e}")
            continue
    
    print(f"\n{'=' * 60}")
    print(f"  BATCH COMPLETE: {len(results)}/{num_reels} reels generated")
    print(f"{'=' * 60}")
    
    return results


def schedule_to_buffer(reels: List[Dict]) -> bool:
    print("\n" + "=" * 60)
    print("  SCHEDULING TO BUFFER")
    print("=" * 60)
    
    profile = get_instagram_channel()
    if not profile:
        print("\n  ERROR: No Instagram channel connected to Buffer!")
        print("  Please connect your Instagram account in Buffer first.")
        return False
    
    profile_id = profile["id"]
    
    video_paths = [r["video_path"] for r in reels]
    captions = [r["caption"] for r in reels]
    schedule_times = generate_schedule_times(len(reels))
    
    results = schedule_batch(
        channel_id=profile_id,
        video_paths=video_paths,
        captions=captions,
        scheduled_times=schedule_times,
    )
    
    success_count = sum(1 for r in results if "error" not in r)
    
    if success_count == len(reels):
        print(f"\n  ✓ All {len(reels)} reels scheduled successfully!")
        return True
    else:
        print(f"\n  ⚠ Only {success_count}/{len(reels)} reels scheduled")
        return False


def save_reel_manifest(reels: List[Dict], manifest_path: str):
    manifest = {
        "batch_generated": datetime.now().isoformat(),
        "total_reels": len(reels),
        "reels": reels,
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n  Manifest saved: {manifest_path}")


def cleanup_reels(reels: List[Dict]):
    deleted = 0
    for r in reels:
        path = r.get("video_path")
        if path and os.path.exists(path):
            try:
                os.remove(path)
                deleted += 1
            except Exception:
                pass
    manifest = os.path.join(OUTPUT_DIR, "reel_manifest.json")
    if os.path.exists(manifest):
        os.remove(manifest)
    print(f"  Cleaned up {deleted} video files from disk")


def run_full_cycle():
    start_time = datetime.now()
    
    print("\n" + "🎮" * 30)
    print("  MINECRAFT REEL AUTOMATION - FULL CYCLE")
    print("🎮" * 30)
    print(f"\n  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n[STEP 1/4] Generating reels...")
    reels = generate_batch(BATCH_SIZE)
    
    if not reels:
        print("\n  ERROR: No reels generated!")
        return False
    
    manifest_path = os.path.join(OUTPUT_DIR, "reel_manifest.json")
    save_reel_manifest(reels, manifest_path)
    
    print("\n[STEP 2/4] Scheduling to Buffer...")
    schedule_success = schedule_to_buffer(reels)
    
    print("\n[STEP 3/4] Cleaning up local files...")
    if schedule_success:
        cleanup_reels(reels)
    else:
        print("  Skipped — some reels failed to schedule, keeping files")
    
    print("\n[STEP 4/4] Sending notifications...")
    send_reel_ready_notification(
        reel_count=len(reels),
        output_dir=OUTPUT_DIR,
    )
    
    reminder_date = datetime.now() + timedelta(days=5)
    print(f"\n  📱 Reminder: run this BAT file again on {reminder_date.strftime('%Y-%m-%d')}")
    
    duration = datetime.now() - start_time
    minutes = duration.total_seconds() / 60
    
    print("\n" + "=" * 60)
    print(f"  CYCLE COMPLETE!")
    print(f"  Duration: {minutes:.1f} minutes")
    print(f"  Reels generated: {len(reels)}")
    print(f"  Scheduled to Buffer: {'✓' if schedule_success else '✗'}")
    print(f"  Local files deleted: {'✓' if schedule_success else '✗'}")
    print(f"  Next run: {reminder_date.strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    return schedule_success


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--generate-only":
            reels = generate_batch(BATCH_SIZE)
            manifest_path = os.path.join(OUTPUT_DIR, "reel_manifest.json")
            save_reel_manifest(reels, manifest_path)
        elif sys.argv[1] == "--schedule-only":
            manifest_path = os.path.join(OUTPUT_DIR, "reel_manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                schedule_to_buffer(manifest["reels"])
            else:
                print("No manifest found. Run with no args first.")
        elif sys.argv[1] == "--test-notify":
            from src.phone_notify import send_phone_notification
            send_phone_notification(
                title="Test from BAT",
                message="Automation is working!",
            )
        else:
            print("Usage:")
            print("  python batch_generate.py           # Full cycle")
            print("  python batch_generate.py --generate-only")
            print("  python batch_generate.py --schedule-only")
            print("  python batch_generate.py --test-notify")
    else:
        run_full_cycle()
