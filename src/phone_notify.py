"""ntfy.sh phone notifications. Setup: install ntfy app, subscribe to topic, set NTFY_TOPIC in config.py."""

import requests
from .config import NTFY_TOPIC, NTFY_SERVER


def send_phone_notification(title: str, message: str, priority: str = "high"):
    url = f"{NTFY_SERVER}/{NTFY_TOPIC}"
    
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": "rotating_light,minecraft",
    }
    
    response = requests.post(url, data=message.encode("utf-8"), headers=headers)
    response.raise_for_status()
    print(f"  Phone notification sent: {title}")
    return True


def send_reel_ready_notification(reel_count: int, output_dir: str):
    send_phone_notification(
        title=f"🎮 {reel_count} Reels Ready!",
        message=f"Batch complete! {reel_count} reels generated.\n\n"
                f"Next step: Run the Buffer scheduler.\n"
                f"Output: {output_dir}\n\n"
                f"Open the BAT file to schedule them to Instagram.",
        priority="high",
    )


def send_reminder_notification(days_since: int = 5):
    send_phone_notification(
        title="⏰ Time to Generate Reels!",
        message=f"It's been {days_since} days since your last batch.\n\n"
                f"Your Instagram queue is running low!\n"
                f"Run the BAT file to generate 10 more reels.",
        priority="urgent",
    )


if __name__ == "__main__":
    send_phone_notification(
        title="Test Notification",
        message="If you see this, ntfy.sh is working!",
        priority="default",
    )
    print("Test sent!")
