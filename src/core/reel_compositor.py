import os
import subprocess
import json

def get_audio_duration(audio_path: str) -> float:
    """Uses ffprobe to get the exact duration of an audio file in seconds."""
    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        audio_path
    ]
    try:
        output = subprocess.check_output(cmd).decode("utf-8").strip()
        return float(output)
    except Exception as e:
        print(f"Error getting duration for {audio_path}: {e}")
        return 5.0 # fallback

def escape_ffmpeg_text(text: str) -> str:
    """Escapes text for ffmpeg drawtext filter (when using text=).
       Not needed if using textfile=, but kept for legacy."""
    text = text.replace('\\', '\\\\')
    text = text.replace(':', '\\:')
    text = text.replace("'", "\\'")
    return text

import re

def create_slide_ass(caption: str, duration: float, output_ass: str):
    # Parse markdown bold/asterisks for highlights
    # *word* -> {\c&H1AB4F4&}word{\c&HFFFFFF&} (Yellowish #F4B41A in BGR)
    def replacer(match):
        return r"{\c&H1AB4F4&}" + match.group(1) + r"{\c&HFFFFFF&}"
    
    clean_caption = caption.replace('\n', ' ')
    rich_caption = re.sub(r'\*(.*?)\*', replacer, clean_caption)
    
    # If no asterisks were found but we want the blue text fallback? 
    # The user asked for "blueish color for the normal text and yellowish text for the important words"
    # Actually, they also said "the text is wheite", and the background is a block box.
    # Let's make the background block box Dark Blue (#143d59) -> &H593D14 in BGR.
    
    def format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds * 100) % 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    t_in_start = 0.0
    t_in_end = min(0.7, duration / 3.0)
    
    t_out_start = max(duration - 0.7, duration * 2.0 / 3.0)
    t_out_end = duration

    # BorderStyle: 4 = Opaque box
    # OutlineColour: &H40593D14& (Dark blue box, slight transparency)
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ReelStyle,Roboto Black,65,&H00FFFFFF,&H000000FF,&H40593D14,&H80000000,0,0,0,0,100,100,0,0,4,20,0,2,10,10,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{format_time(t_in_start)},{format_time(t_in_end)},ReelStyle,,0,0,0,,{{\\move(1620,1670,540,1670)}}{rich_caption}
Dialogue: 0,{format_time(t_in_end)},{format_time(t_out_start)},ReelStyle,,0,0,0,,{{\\pos(540,1670)}}{rich_caption}
Dialogue: 0,{format_time(t_out_start)},{format_time(t_out_end)},ReelStyle,,0,0,0,,{{\\move(540,1670,-540,1670)}}{rich_caption}
"""
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(ass_content)
    return output_ass

def compile_slide(slide_index: int, image_path: str, audio_path: str, caption: str, output_path: str, font_path: str) -> str:
    """
    Compiles a single slide (image + audio + sliding text).
    """
    duration = get_audio_duration(audio_path)
    
    # Generate the rich-text ASS subtitle file
    ass_path = os.path.join(os.path.dirname(output_path), f"slide_{slide_index}.ass")
    create_slide_ass(caption, duration, ass_path)
    
    # Use relative paths for subtitles filter to avoid Windows absolute path escaping issues in ffmpeg
    ass_path_ff = ass_path.replace("\\", "/")
    
    # fontsdir tells libass where to find custom fonts like Roboto Black
    fonts_dir_ff = "assets/fonts"
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "30", "-i", image_path,
        "-i", audio_path,
        "-vf", f"subtitles='{ass_path_ff}':fontsdir='{fonts_dir_ff}'",
        "-c:v", "libx264", "-preset", "fast", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", # End when audio ends
        "-pix_fmt", "yuv420p",
        output_path
    ]
    
    print(f"[{slide_index}] Compiling slide (Duration: {duration:.2f}s)...")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[{slide_index}] Saved {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"[{slide_index}] Error compiling slide: {e}")
        return None

def compile_reel(slide_paths: list, output_path: str) -> str:
    """
    Concatenates all individual slide MP4s into the final Reel MP4.
    """
    print(f"Concatenating {len(slide_paths)} slides into final Reel...")
    
    list_path = os.path.join(os.path.dirname(output_path), "concat_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for path in slide_paths:
            # ffmpeg concat evaluates paths relative to the concat_list.txt directory!
            # Since both are in drafts/reels, just use the basename.
            safe_path = os.path.basename(path)
            f.write(f"file '{safe_path}'\n")
            
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Final Reel saved to {output_path}")
        
        # Cleanup intermediate list
        if os.path.exists(list_path):
            os.remove(list_path)
            
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error concatenating Reel: {e}")
        return None

if __name__ == "__main__":
    # Test script
    print("reels_compositor loaded.")
