import os
import random
import asyncio
import subprocess
import edge_tts
from edge_tts import SubMaker
from core.llm_processor import model, extract_text

# The two voices approved by the user
VOICES = [
    "en-US-JennyNeural", 
    "en-US-SteffanNeural"
]

def draft_video_script(curated_articles):
    """
    Drafts a highly engaging 15-30 second spoken script tailored for YouTube Shorts / TikTok.
    """
    if not curated_articles:
        return None

    print("\n[Video Engine] Drafting short-form video script...")
    prompt = (
        "You are an expert short-form video scriptwriter for TikTok and YouTube Shorts.\n"
        "Write a punchy, high-energy 20-second VoiceOver script based on this AI news.\n"
        "Guidelines:\n"
        "- NO hashtags, NO emojis, NO markdown formatting (like asterisks).\n"
        "- Write strictly the words to be spoken by the narrator.\n"
        "- Start with a massive hook that stops the scroll.\n"
        "- Deliver the value quickly.\n"
        "- End with a question to drive comments.\n\n"
        "News:\n"
    )
    for article in curated_articles:
        prompt += f"- {article['title']}: {article['summary']}\n"
        
    try:
        response = model.generate_content(prompt)
        text = extract_text(response).strip()
        # Clean any accidental markdown just in case
        return text.replace("**", "").replace("*", "")
    except Exception as e:
        print(f"Error generating video script: {e}")
        return None

import json
import subprocess
import os
import random
from core.kinetic_captions import generate_kinetic_captions

def parse_vtt_to_whisper_json(vtt_path):
    """Interpolate sentence-level VTT into word-level timings."""
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.strip().split('\n\n')
    segments = []
    
    def time_to_sec(t_str):
        parts = t_str.strip().split(':')
        if len(parts) == 3:
            h, m, s = parts
        else:
            h = 0
            m, s = parts
            
        if ',' in s:
            sec, ms = s.split(',')
        elif '.' in s:
            sec, ms = s.split('.')
        else:
            sec, ms = s, 0
            
        return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000.0

    for block in blocks:
        lines = block.split('\n')
        time_line = next((l for l in lines if '-->' in l), None)
        if not time_line: continue
        
        text_line = ' '.join(lines[lines.index(time_line)+1:])
        start_str, end_str = time_line.split('-->')
        
        # Shift timestamps BACK by 150ms to fix the "audio is ahead" sync issue
        offset = -0.150
        start_sec = max(0, time_to_sec(start_str) + offset)
        end_sec = max(0.1, time_to_sec(end_str) + offset)
        
        words = text_line.split()
        if not words: continue
        
        duration = end_sec - start_sec
        time_per_word = duration / len(words)
        
        word_dicts = []
        curr_time = start_sec
        for w in words:
            word_dicts.append({
                "word": w,
                "start": curr_time,
                "end": curr_time + time_per_word
            })
            curr_time += time_per_word
            
        segments.append({"words": word_dicts})
        
    return {"segments": segments}

def generate_audio(text, output_path="drafts/voiceover.mp3", subs_path="drafts/subs.ass"):
    """Uses edge-tts CLI to generate audio/vtt, then converts to Kinetic ASS captions."""
    voice = random.choice(VOICES)
    print(f"[Video Engine] Selected Voice: {voice}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    vtt_path = subs_path.replace('.ass', '.vtt')
    
    python_exe = r"C:\Users\frasheed\miniconda3\python.exe"
    command = [
        python_exe, "-m", "edge_tts",
        "--text", text,
        "--voice", voice,
        "--write-media", output_path,
        "--write-subtitles", vtt_path
    ]
    
    print("[Video Engine] Calling Edge TTS CLI...")
    subprocess.run(command, check=True)
    
    print("[Video Engine] Interpolating VTT to Word-Level JSON...")
    whisper_json = parse_vtt_to_whisper_json(vtt_path)
    
    print("[Video Engine] Generating Kinetic ASS Captions...")
    generate_kinetic_captions(whisper_json, subs_path, style='karaoke', platform='tiktok')
    
    return output_path, subs_path

def compile_video(image_path, audio_path, subs_path, output_path="drafts/final_video.mp4"):
    """
    Uses ffmpeg to combine image, audio, live waveform, and dynamic center captions.
    """
    print("[Video Engine] Stitching image, audio, waveform, and dynamic captions...")
    
    # Ensure paths are absolute so ffmpeg doesn't get confused
    img_abs = os.path.abspath(image_path)
    aud_abs = os.path.abspath(audio_path)
    out_abs = os.path.abspath(output_path)
    
    # Convert backslashes to forward slashes for the subtitle path.
    # VERY IMPORTANT: FFmpeg on Windows fails to parse absolute paths in ASS/subtitles filters 
    # if they contain spaces. Use the relative path to bypass the bug.
    sub_rel = subs_path.replace('\\', '/')
    
    # Use the absolute path to ffmpeg since it's failing in the command prompt
    FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
    
    # Complex Filter Graph:
    # 1. Create waveform
    # 2. Overlay waveform below logo (x=40, y=90)
    # 3. Burn Kinetic ASS Subtitles using the 'ass' filter!
    filter_complex = (
        f"[1:a]showwaves=s=300x50:mode=cline:colors=white[wave];"
        f"[0:v][wave]overlay=40:90[v_out];"
        f"[v_out]ass='{sub_rel}'[final]"
    )
    
    command = [
        FFMPEG_PATH, "-y",
        "-loop", "1",
        "-i", img_abs,
        "-i", aud_abs,
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out_abs
    ]
    
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"[Video Engine] ✅ Video compiled successfully: {out_abs}")
            return out_abs
        else:
            print("[Video Engine] FFmpeg error:")
            print(result.stderr.decode("utf-8"))
            return None
    except FileNotFoundError:
        print("[Video Engine] FATAL ERROR: FFmpeg is not installed or not in your system PATH.")
        return None
