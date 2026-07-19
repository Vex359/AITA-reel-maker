#!/usr/bin/env python3
"""Entry point for Minecraft Reel Automation."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import generate_reel, generate_reel_with_story


def main():
    """Main entry point."""
    
    # Check for custom story argument
    if len(sys.argv) > 1:
        story_file = sys.argv[1]
        
        if os.path.exists(story_file):
            # Read story from file
            with open(story_file, "r", encoding="utf-8") as f:
                story_text = f.read()
            
            print(f"Using custom story from: {story_file}")
            output = generate_reel_with_story(story_text)
        else:
            # Treat argument as story text
            print(f"Using provided text as story")
            output = generate_reel_with_story(story_file)
    else:
        # Default: fetch from Reddit
        print("Fetching story from Reddit...")
        output = generate_reel()
    
    print(f"\nDone! Video saved to: {output}")


if __name__ == "__main__":
    main()
