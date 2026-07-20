"""Buffer GraphQL API for scheduling Instagram Reels. Uses personal API key from publish.buffer.com/settings/api."""

import time
import random
import requests
from datetime import datetime, timedelta
from typing import Optional

from .config import BUFFER_ACCESS_TOKEN, POSTS_PER_DAY, BATCH_SIZE

BUFFER_API_BASE = "https://api.buffer.com"


def graphql_query(query: str, variables: dict = None) -> dict:
    headers = {
        "Authorization": f"Bearer {BUFFER_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(BUFFER_API_BASE, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def get_organizations() -> list:
    query = """
    query GetOrganizations {
        account {
            organizations {
                id
                name
                ownerEmail
            }
        }
    }
    """
    result = graphql_query(query)
    
    if "errors" in result:
        print(f"  API Error: {result['errors']}")
        return []
    
    orgs = result.get("data", {}).get("account", {}).get("organizations", [])
    print(f"  Found {len(orgs)} organizations:")
    for org in orgs:
        print(f"    - {org['name']} (ID: {org['id']})")
    
    return orgs


def get_channels(org_id: str) -> list:
    query = """
    query GetChannels {
        channels(input: {organizationId: "%s"}) {
            id
            name
            displayName
            service
            avatar
            isQueuePaused
        }
    }
    """ % org_id
    result = graphql_query(query)
    
    if "errors" in result:
        print(f"  API Error: {result['errors']}")
        return []
    
    channels = result.get("data", {}).get("channels", [])
    print(f"  Found {len(channels)} connected channels:")
    for ch in channels:
        print(f"    - {ch['service']}: @{ch.get('displayName', 'unknown')} (ID: {ch['id']})")
    
    return channels


def get_instagram_channel() -> Optional[dict]:
    orgs = get_organizations()
    if not orgs:
        print("  WARNING: No organizations found!")
        return None
    
    for org in orgs:
        channels = get_channels(org["id"])
        for ch in channels:
            if ch.get("service") == "instagram":
                return ch
    
    print("  WARNING: No Instagram channel found in Buffer!")
    return None


def create_post(channel_id: str, text: str, video_url: str, scheduled_at: datetime) -> dict:
    due_at = scheduled_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    query = """
mutation CreatePost {
  createPost(input: {
    text: "%s",
    channelId: "%s",
    schedulingType: automatic,
    mode: customScheduled,
    dueAt: "%s",
    assets: [{
      video: {
        url: "%s"
      }
    }],
    metadata: { instagram: { type: reel, shouldShareToFeed: true } }
  }) {
    ... on PostActionSuccess {
      post {
        id
        text
      }
    }
    ... on MutationError {
      message
    }
  }
}
""" % (text.replace('"', '\\"'), channel_id, due_at, video_url)
    
    result = graphql_query(query)
    
    if "errors" in result:
        print(f"  API Error: {result['errors']}")
        return {"error": result["errors"]}
    
    post_data = result.get("data", {}).get("createPost", {})
    
    if "message" in post_data:
        print(f"  Mutation Error: {post_data['message']}")
        return {"error": post_data["message"]}
    
    post = post_data.get("post", {})
    print(f"  Scheduled: {scheduled_at.strftime('%Y-%m-%d %H:%M')} | {text[:30]}...")
    return post


def generate_schedule_times(num_posts: int, start_date: Optional[datetime] = None) -> list:
    if start_date is None:
        start_date = datetime.now() + timedelta(days=1)
        start_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
    
    times = []
    posts_per_day = POSTS_PER_DAY
    days_needed = (num_posts + posts_per_day - 1) // posts_per_day
    
    base_morning = (9, 0)
    base_evening = (19, 0)
    
    post_num = 0
    for day in range(days_needed):
        current_date = start_date + timedelta(days=day)
        
        for slot in range(posts_per_day):
            if post_num >= num_posts:
                break
            
            offset_minutes = random.randint(-120, 120)
            
            if slot == 0:
                base_hour, base_min = base_morning
            else:
                base_hour, base_min = base_evening
            
            post_time = current_date.replace(
                hour=base_hour,
                minute=base_min
            ) + timedelta(minutes=offset_minutes)
            
            if post_time.hour < 6:
                post_time = post_time.replace(hour=6, minute=0)
            elif post_time.hour >= 22:
                post_time = post_time.replace(hour=21, minute=30)
            
            times.append(post_time)
            post_num += 1
        
        if post_num >= num_posts:
            break
    
    print("\n  Generated Schedule:")
    for i, t in enumerate(times, 1):
        print(f"    Post {i}: {t.strftime('%Y-%m-%d %H:%M')}")
    
    return times


def schedule_batch(channel_id: str, video_paths: list, captions: list, scheduled_times: list) -> list:
    from .cloudinary_uploader import upload_video
    
    results = []
    
    print(f"\n{'='*60}")
    print(f"SCHEDULING {len(captions)} REELS TO BUFFER")
    print(f"{'='*60}")
    
    for i, (video_path, caption, sched_time) in enumerate(
        zip(video_paths, captions, scheduled_times), 1
    ):
        print(f"\n[{i}/{len(captions)}] Uploading and scheduling reel...")
        
        try:
            video_url = upload_video(video_path)
            
            result = create_post(
                channel_id=channel_id,
                text=caption,
                video_url=video_url,
                scheduled_at=sched_time,
            )
            results.append(result)
            
            if i < len(captions):
                time.sleep(1)
                
        except Exception as e:
            print(f"  ERROR scheduling reel {i}: {e}")
            results.append({"error": str(e)})
    
    print(f"\n{'='*60}")
    success_count = sum(1 for r in results if "error" not in r)
    print(f"SCHEDULED: {success_count}/{len(captions)} reels")
    print(f"{'='*60}")
    
    return results


if __name__ == "__main__":
    print("Testing Buffer GraphQL API connection...")
    try:
        orgs = get_organizations()
        print(f"\nFound {len(orgs)} organizations.")
        
        if orgs:
            channels = get_channels(orgs[0]["id"])
            print(f"Found {len(channels)} channels in first org.")
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure BUFFER_ACCESS_TOKEN is set in config.py")
