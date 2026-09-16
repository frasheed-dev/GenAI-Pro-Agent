"""
test_edge_video.py
───────────────────
Standalone test script combining MoneyPrinterTurbo's Edge TTS voice synthesis
and FFmpeg composition patterns with GenAI Pro's visual news cards.

Generates:
  1. Voiceover audio via Microsoft Edge TTS (en-US-ChristopherNeural) - $0 cost.
  2. Word-level SRT/ASS subtitles.
  3. A 9:16 vertical 1080x1920 MP4 reel video combining the news card, voiceover, and captions.

Usage:
  python tests/test_edge_video.py
"""

import os
import sys
import io
import asyncio
import subprocess
from PIL import Image

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from core.image_generator import create_slide_image

AUDIO_PATH = "drafts/test_reel_audio.mp3"
SUB_PATH = "test_reel_subs.srt"
BG_IMAGE_PATH = "drafts/test_reel_bg.png"
OUTPUT_VIDEO_PATH = "drafts/test_genai_pro_reel.mp4"

SAMPLE_SCRIPT = (
    "Meta has hit a wall on AI agent development. Zuckerberg admitted that progress is significantly "
    "slower than internal roadmaps anticipated. Meanwhile, startups are funneling millions into native "
    "AI suites to challenge tech giants. The lesson is clear: scaling intelligence is harder than scaling a social network."
)

SAMPLE_HEADLINE = "Meta Hits Wall on *AI Agent* Progress as *Roadmap Lags*"

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

def render_video_with_ffmpeg():
    print("🎬 Stitching 9:16 Vertical Reel Video with FFmpeg...")
    
    # Explicit filename parameter for FFmpeg libass filter
    sub_filter = "subtitles=filename=test_reel_subs.srt"
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", BG_IMAGE_PATH,
        "-i", AUDIO_PATH,
        "-vf", sub_filter,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        OUTPUT_VIDEO_PATH
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"❌ FFmpeg error: {res.stderr}")
        return None
        
    print(f"   ✅ Successfully rendered vertical MP4 reel to {OUTPUT_VIDEO_PATH}")
    print(f"   ✅ File size: {os.path.getsize(OUTPUT_VIDEO_PATH)/1024/1024:.2f} MB")
    return OUTPUT_VIDEO_PATH

def main():
    print("═" * 60)
    print("TESTING MONEYPRINTERTURBO-INSPIRED SHORT-FORM VIDEO PIPELINE")
    print("═" * 60)
    
    # 1. Generate 9:16 Background Graphic Asset (1080x1920)
    print("\n1. Creating 9:16 Vertical Graphic Asset...")
    create_slide_image(
        image_prompt="Stylized globe surrounded by glowing digital circuits and red off switch",
        slide_index=1,
        total_slides=1,
        output_path=BG_IMAGE_PATH,
        force_fallback=True
    )
    assert os.path.exists(BG_IMAGE_PATH), "Background graphic failed to generate"
    
    # 2. Run Edge TTS Voiceover & Subtitle Generation
    print("\n2. Generating Audio & Timed Subtitles...")
    asyncio.run(generate_tts_and_subtitles(SAMPLE_SCRIPT))
    assert os.path.exists(AUDIO_PATH), "Audio file failed to generate"
    assert os.path.exists(SUB_PATH), "Subtitle file failed to generate"
    
    # 3. Render 9:16 Vertical MP4 Video
    print("\n3. Rendering Video...")
    video_file = render_video_with_ffmpeg()
    assert video_file and os.path.exists(video_file), "Video rendering failed"
    
    print("\n" + "═" * 60)
    print(f"🎉 SHORT-FORM REEL TEST COMPLETE!")
    print(f"   Video Location: {os.path.abspath(OUTPUT_VIDEO_PATH)}")
    print("═" * 60)

if __name__ == "__main__":
    main()
