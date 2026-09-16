"""
test_stitched_video.py
───────────────────────
Demonstrates MULTI-CLIP VIDEO STITCHING for GenAI Pro short-form reels.

What this test does:
  1. Generates 3 distinct vertical 9:16 visual cards (or fetches stock clips) for 3 scenes:
     - Scene 1 (0-7s): Headline Card ("Meta Hits Wall on AI Agent Progress")
     - Scene 2 (7-14s): Data & Context Card ("Zuckerberg Admits Roadmap Lags")
     - Scene 3 (14-21s): Strategic Takeaway Card ("Scaling Intelligence vs. Social Networks")
  2. Synthesizes Edge TTS voiceover audio & timed subtitles.
  3. Uses FFmpeg to STITCH the 3 visual scenes sequentially with smooth transitions.
  4. Overlays burnt-in captions on top of the stitched video sequence.
"""

import os
import sys
import io
import asyncio
import subprocess
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from core.image_generator import create_slide_image

AUDIO_PATH = "drafts/test_stitched_audio.mp3"
SUB_PATH = "test_stitched_subs.srt"
OUTPUT_VIDEO_PATH = "drafts/test_genai_pro_stitched_reel.mp4"

SLIDE_PATHS = [
    "drafts/test_slide_1.png",
    "drafts/test_slide_2.png",
    "drafts/test_slide_3.png"
]

SAMPLE_SCRIPT = (
    "Meta has hit a wall on AI agent development. Zuckerberg admitted that progress is significantly "
    "slower than internal roadmaps anticipated. Meanwhile, startups are funneling millions into native "
    "AI suites to challenge tech giants. The lesson is clear: scaling intelligence is harder than scaling a social network."
)

async def generate_tts_and_subtitles(text: str, voice: str = "en-US-ChristopherNeural"):
    import edge_tts
    print(f"🎙️ Generating voiceover with Microsoft Edge TTS ({voice})...")
    
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    
    with open(AUDIO_PATH, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
                
    srt_content = submaker.get_srt()
    with open(SUB_PATH, "w", encoding="utf-8") as f:
        f.write(srt_content)
        
    print(f"   ✅ Saved audio to {AUDIO_PATH} ({os.path.getsize(AUDIO_PATH)/1024:.1f} KB)")
    print(f"   ✅ Saved subtitles to {SUB_PATH} ({os.path.getsize(SUB_PATH)} bytes)")

def create_multi_scene_slides():
    print("🎨 Creating 3 Distinct Visual Cards for Multi-Scene Video Stitching...")
    
    # Scene 1: Headline
    create_slide_image(
        image_prompt="Meta logo surrounded by wall barrier",
        slide_index=1,
        total_slides=3,
        output_path=SLIDE_PATHS[0],
        force_fallback=True
    )
    
    # Scene 2: Context / Data
    create_slide_image(
        image_prompt="Financial chart showing AI startup funding growth",
        slide_index=2,
        total_slides=3,
        output_path=SLIDE_PATHS[1],
        force_fallback=True
    )
    
    # Scene 3: Key Takeaway
    create_slide_image(
        image_prompt="Glowing AI brain interconnected with global network",
        slide_index=3,
        total_slides=3,
        output_path=SLIDE_PATHS[2],
        force_fallback=True
    )

def render_stitched_video():
    print("🎬 Stitching 3 Scenes & Subtitles into Final MP4 Reel with FFmpeg...")
    
    # Each scene will play for ~7.2 seconds (total 21.6s matching audio length)
    scene_duration = 7.2
    
    # FFmpeg complex filter:
    # 1. Loop each of the 3 slide images for 7.2 seconds
    # 2. Concat the 3 visual scenes sequentially: [0:v][1:v][2:v] concat=n=3:v=1:a=0 [v_concat]
    # 3. Apply subtitles filter: [v_concat] subtitles=test_stitched_subs.srt [v_final]
    filter_complex = (
        f"[0:v]loop=loop={int(scene_duration*25)}:size=1:start=0,setpts=N/25/TB[v0];"
        f"[1:v]loop=loop={int(scene_duration*25)}:size=1:start=0,setpts=N/25/TB[v1];"
        f"[2:v]loop=loop={int(scene_duration*25)}:size=1:start=0,setpts=N/25/TB[v2];"
        f"[v0][v1][v2]concat=n=3:v=1:a=0[v_concat];"
        f"[v_concat]subtitles={SUB_PATH}:force_style='Fontname=Arial,Fontsize=22,PrimaryColour=&H00FFFFFF&,"
        f"OutlineColour=&H00000000&,BackColour=&H80143D59&,BorderStyle=4,Outline=2,Shadow=0,MarginV=120,Alignment=2'[v_final]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", SLIDE_PATHS[0],
        "-i", SLIDE_PATHS[1],
        "-i", SLIDE_PATHS[2],
        "-i", AUDIO_PATH,
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "3:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        OUTPUT_VIDEO_PATH
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"❌ FFmpeg stitching error: {res.stderr}")
        return None
        
    print(f"   ✅ Successfully stitched multi-scene MP4 reel to {OUTPUT_VIDEO_PATH}")
    print(f"   ✅ File size: {os.path.getsize(OUTPUT_VIDEO_PATH)/1024/1024:.2f} MB")
    return OUTPUT_VIDEO_PATH

def main():
    print("═" * 60)
    print("MULTI-SCENE VIDEO STITCHING TEST (GENAI PRO REELS PIPELINE)")
    print("═" * 60)
    
    # 1. Create 3 distinct visual cards
    create_multi_scene_slides()
    
    # 2. Generate Audio & Timed Subtitles
    asyncio.run(generate_tts_and_subtitles(SAMPLE_SCRIPT))
    
    # 3. Stitch Scenes into Video Reel
    video_file = render_stitched_video()
    assert video_file and os.path.exists(video_file), "Stitched video rendering failed"
    
    print("\n" + "═" * 60)
    print(f"🎉 MULTI-SCENE STITCHED REEL TEST COMPLETE!")
    print(f"   Video Location: {os.path.abspath(OUTPUT_VIDEO_PATH)}")
    print("═" * 60)

if __name__ == "__main__":
    main()
