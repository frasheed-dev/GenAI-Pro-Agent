"""
test_real_broll_video.py
────────────────────────
Stitches 3 REAL MOVING B-ROLL VIDEO CLIPS (MP4) sequentially into a 9:16 vertical short-form reel.

What this test does:
  1. Uses 3 real moving HD video clips (drafts/broll_clip_1.mp4, clip_2.mp4, clip_3.mp4).
  2. Scales & crops each video clip to 9:16 vertical resolution (1080x1920).
  3. Trims & concatenates the 3 video clips sequentially (7.2s each) into a single moving background video stream.
  4. Overlays Microsoft Edge TTS voiceover audio & timed ASS/SRT captions on top of the moving footage.
  5. Renders final MP4 video reel to drafts/test_real_broll_reel.mp4.
"""

import os
import sys
import io
import asyncio
import subprocess

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

AUDIO_PATH = "drafts/test_broll_audio.mp3"
SUB_PATH = "test_broll_subs.srt"
OUTPUT_VIDEO_PATH = "drafts/test_real_broll_reel.mp4"

CLIP_PATHS = [
    "drafts/broll_clip_1.mp4",
    "drafts/broll_clip_2.mp4",
    "drafts/broll_clip_3.mp4"
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

def render_broll_stitched_video():
    print("🎬 Stitching 3 Moving B-Roll MP4 Video Clips with FFmpeg...")
    
    # 7.2s per clip (total ~21.6s)
    clip_dur = 7.2
    
    # Filter graph:
    # 1. Trim & scale clip 1 to 1080x1920
    # 2. Trim & scale clip 2 to 1080x1920
    # 3. Trim & scale clip 3 to 1080x1920
    # 4. Concat all 3 video streams -> [v_concat]
    # 5. Burn in subtitles with high-contrast outline & background box -> [v_final]
    filter_complex = (
        f"[0:v]trim=duration={clip_dur},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setpts=PTS-STARTPTS[v0];"
        f"[1:v]trim=duration={clip_dur},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setpts=PTS-STARTPTS[v1];"
        f"[2:v]trim=duration={clip_dur},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setpts=PTS-STARTPTS[v2];"
        f"[v0][v1][v2]concat=n=3:v=1:a=0[v_concat];"
        f"[v_concat]subtitles={SUB_PATH}:force_style='Fontname=Arial,Fontsize=24,PrimaryColour=&H00FFFFFF&,"
        f"OutlineColour=&H00000000&,BackColour=&H80000000&,BorderStyle=4,Outline=2,Shadow=1,MarginV=180,Alignment=2'[v_final]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", CLIP_PATHS[0],
        "-i", CLIP_PATHS[1],
        "-i", CLIP_PATHS[2],
        "-i", AUDIO_PATH,
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "3:a",
        "-c:v", "libx264",
        "-preset", "fast",
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
        
    print(f"   ✅ Successfully rendered moving B-roll MP4 reel to {OUTPUT_VIDEO_PATH}")
    print(f"   ✅ File size: {os.path.getsize(OUTPUT_VIDEO_PATH)/1024/1024:.2f} MB")
    return OUTPUT_VIDEO_PATH

def main():
    print("═" * 60)
    print("REAL MOVING B-ROLL VIDEO STITCHING TEST (GENAI PRO REELS PIPELINE)")
    print("═" * 60)
    
    for clip in CLIP_PATHS:
        assert os.path.exists(clip), f"Missing B-roll clip: {clip}"
        
    # 1. Generate Voiceover & Subtitles
    asyncio.run(generate_tts_and_subtitles(SAMPLE_SCRIPT))
    
    # 2. Stitch Moving B-Roll Clips & Audio into Vertical Reel
    video_file = render_broll_stitched_video()
    assert video_file and os.path.exists(video_file), "B-roll video rendering failed"
    
    print("\n" + "═" * 60)
    print(f"🎉 REAL MOVING B-ROLL REEL TEST COMPLETE!")
    print(f"   Video Location: {os.path.abspath(OUTPUT_VIDEO_PATH)}")
    print("═" * 60)

if __name__ == "__main__":
    main()
