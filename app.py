import streamlit as st
import os
import glob
from datetime import datetime

st.set_page_config(page_title="Minecraft Reel Generator", layout="centered")

st.title("Minecraft Reel Generator")
st.markdown("Generate Minecraft parkour reels with Reddit stories, memes, and AI voice.")

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

if "generating" not in st.session_state:
    st.session_state.generating = False

st.subheader("Paste Reddit Post")
title_input = st.text_input("Post Title", placeholder="e.g. AITA for refusing to give up my plane seat?")
body_input = st.text_area("Post Body", height=200, placeholder="Paste the full Reddit post here...")

col1, col2 = st.columns([1, 1])

with col1:
    generate_disabled = st.session_state.generating or not body_input.strip()
    if st.button("Generate Reel", type="primary", disabled=generate_disabled):
        st.session_state.generating = True
        st.session_state.custom_title = title_input.strip() if title_input.strip() else "Reddit Post"
        st.session_state.custom_body = body_input.strip()
        st.rerun()

with col2:
    if st.button("Refresh List"):
        st.rerun()

if st.session_state.generating:
    st.info("Generating reel... This may take 1-2 minutes.")
    progress = st.progress(0, text="Starting...")
    
    try:
        from src.main import generate_reel_with_story
        
        progress.progress(10, text="Generating script...")
        progress.progress(25, text="Extracting keywords...")
        progress.progress(40, text="Fetching memes...")
        progress.progress(55, text="Generating voice...")
        progress.progress(70, text="Composing video...")
        
        output_path = generate_reel_with_story(
            story_text=st.session_state.custom_body,
            title=st.session_state.custom_title,
        )
        
        progress.progress(100, text="Done!")
        st.session_state.generating = False
        st.success(f"Reel generated: {os.path.basename(output_path)}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error: {e}")
        st.session_state.generating = False

st.markdown("---")
st.subheader("Generated Reels")

if os.path.exists(output_dir):
    videos = sorted(
        glob.glob(os.path.join(output_dir, "*.mp4")),
        key=os.path.getmtime,
        reverse=True,
    )
    
    if not videos:
        st.info("No reels yet. Paste a Reddit post and click 'Generate Reel' to create one.")
    else:
        cols_per_row = 3
        for i in range(0, len(videos[:12]), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(videos):
                    video_path = videos[idx]
                    filename = os.path.basename(video_path)
                    title = filename.replace(".mp4", "")
                    mod_time = datetime.fromtimestamp(os.path.getmtime(video_path))
                    
                    with col:
                        st.markdown(f"**{title}**")
                        st.caption(mod_time.strftime("%Y-%m-%d %H:%M"))
else:
    st.info("Output folder not found.")
