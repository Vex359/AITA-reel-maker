"""Cloudinary video upload for Buffer scheduling. Free tier: 25GB storage."""

import cloudinary
import cloudinary.uploader
from .config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET


def configure_cloudinary():
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_video(video_path: str) -> str:
    configure_cloudinary()
    
    result = cloudinary.uploader.upload(
        video_path,
        resource_type="video",
        folder="minecraft-reels",
    )
    
    url = result.get("secure_url")
    print(f"  Uploaded: {video_path} -> {url[:50]}...")
    return url


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = upload_video(sys.argv[1])
        print(f"URL: {url}")
    else:
        print("Usage: python -m src.cloudinary_uploader <video_path>")
