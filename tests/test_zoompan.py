import os
import subprocess

def create_zoompan_demo():
    # We will reuse the assets from your previous test
    image_path = "drafts/news_image_universal.png"
    audio_path = "drafts/test_voiceover.mp3"
    vtt_path = "drafts/test_subs.vtt"  # The original, perfectly synced sentence-level VTT
    output_path = "drafts/zoompan_demo.mp4"
    
    # Must use relative path with forward slashes for FFmpeg subtitles
    sub_rel = vtt_path.replace('\\', '/')
    ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
    
    # Complex Filter Strategy:
    # 1. [0:v] zoompan: 
    #    - z='min(zoom+0.0015,1.5)': Zooms in by 0.15% every frame, capping at 1.5x zoom.
    #    - x and y equations keep the camera perfectly centered on the image.
    #    - d=9000 generates enough frames to last up to 6 minutes so it won't freeze early.
    # 2. subtitles:
    #    - Reverting to the raw, native .vtt file means the text is 100% perfectly synced to the voice.
    #    - Alignment=2 (Bottom Center), MarginV=250 (Pushed up slightly so it's easily readable).
    filter_complex = (
        f"[0:v]zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=9000:s=1080x1920[v_bg];"
        f"[v_bg]subtitles='{sub_rel}':force_style='Alignment=2,MarginV=250,Fontname=Arial Black,Fontsize=18,PrimaryColour=&H00FFFF&,Outline=2,Shadow=1'[final]"
    )
    
    command = [
        ffmpeg_path, "-y",
        "-i", image_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]
    
    print("🎬 Generating Zoompan + Native Sync Demo...")
    try:
        subprocess.run(command, check=True)
        print(f"✅ Demo created successfully: {output_path}")
        print("Please watch the video and see how the slow zoom animation looks!")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e}")

if __name__ == "__main__":
    create_zoompan_demo()
