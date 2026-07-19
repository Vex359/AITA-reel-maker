"""TikTok-style word-by-word ASS subtitles with karaoke effect.

Exact same approach as autoclipping project - uses ffmpeg ASS filter
with \\kf karaoke tags for word-by-word highlighting.
"""
import os
import subprocess
from typing import List, Tuple, Dict


ASS_HEADER = """[Script Info]
Title: Auto-generated captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,80,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _group_words_into_chunks(
    words: List[Tuple[str, float, float]],
    max_words: int = 3,
    max_duration: float = 2.0,
) -> List[Tuple[str, float, float, List[Tuple[str, float, float]]]]:
    chunks = []
    current_words = []
    current_word_times = []
    current_start = None
    current_end = None

    for word, start, end in words:
        word = word.strip()
        if not word:
            continue

        if current_words:
            new_duration = end - current_start
            if len(current_words) >= max_words or new_duration > max_duration:
                chunk_text = " ".join(current_words).strip()
                if chunk_text:
                    chunks.append((chunk_text, current_start, current_end, current_word_times))
                current_words = []
                current_word_times = []
                current_start = None
                current_end = None

        current_words.append(word)
        current_word_times.append((word, start, end))
        if current_start is None:
            current_start = start
        current_end = end

    if current_words:
        chunk_text = " ".join(current_words).strip()
        if chunk_text:
            chunks.append((chunk_text, current_start, current_end, current_word_times))

    return chunks


def generate_ass_subtitles(
    words: List[Tuple[str, float, float]],
    max_words: int = 3,
    output_path: str = None,
) -> str:
    chunks = _group_words_into_chunks(words, max_words=max_words)
    lines = [ASS_HEADER.strip()]

    for text, start, end, word_times in chunks:
        start_ts = _format_ass_time(start)
        end_ts = _format_ass_time(end)
        karaoke_words = []
        for w, w_start, w_end in word_times:
            w_escaped = w.replace("\\", "\\\\")
            w_escaped = w_escaped.replace("{", "\\{").replace("}", "\\}")
            w_escaped = w_escaped.upper()
            duration_cs = int((w_end - w_start) * 100)
            karaoke_words.append(f"{{\\kf{duration_cs}}}{w_escaped}")
        karaoke_text = " ".join(karaoke_words)
        lines.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{{\\an5}}{karaoke_text}")

    if output_path is None:
        output_path = os.path.join(os.environ.get("TEMP", r"C:\temp"), "subs.ass")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def burn_subtitles(
    video_path: str,
    ass_path: str,
    output_path: str,
) -> str:
    ass_norm = ass_path.replace('\\', '/')
    ass_escaped = ass_norm.replace(':', '\\:')
    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-i", video_path,
        "-vf", f"subtitles='{ass_escaped}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        output_path,
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg stderr: {result.stderr}")
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    return output_path


def subtitle_video(
    video_path: str,
    subtitle_entries: List[Dict],
    output_path: str = None,
    offset: float = 0.0,
) -> str:
    if output_path is None:
        output_path = video_path

    words = []
    for entry in subtitle_entries:
        text = entry["text"]
        start = entry["start_time"] + offset
        end = entry["end_time"] + offset
        word_list = text.split()
        if not word_list:
            continue
        word_duration = (end - start) / len(word_list)
        for i, word in enumerate(word_list):
            w_start = start + i * word_duration
            w_end = start + (i + 1) * word_duration
            words.append((word, w_start, w_end))

    if not words:
        return video_path

    temp_dir = os.environ.get("TEMP", r"C:\temp")
    os.makedirs(temp_dir, exist_ok=True)
    ass_path = os.path.join(temp_dir, "subs.ass")
    generate_ass_subtitles(words, max_words=3, output_path=ass_path)

    if output_path == video_path:
        temp_out = video_path + ".subtitled.mp4"
        burn_subtitles(video_path, ass_path, temp_out)
        os.replace(temp_out, video_path)
    else:
        burn_subtitles(video_path, ass_path, output_path)

    if os.path.exists(ass_path):
        os.remove(ass_path)

    return output_path
