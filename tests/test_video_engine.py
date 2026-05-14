import os
import sys

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from core.video_generator import generate_audio, compile_video

def run_test():
    print("=== Testing Video Engine (Waveform & Captions) ===")
    
    # We will use the existing universal image from your drafts folder
    image_path = "drafts/news_image_universal.png"
    
    if not os.path.exists(image_path):
        print(f"Error: Could not find {image_path}. Please run main.py first to generate an image.")
        return
        
    test_script = "Stop scrolling! This is a test of the brand new dynamic caption engine and the audio waveform overlay. Generative AI Pro is officially building the most advanced automated media pipeline in the world. Let me know what you think in the comments below!"
    
    print("\n1. Generating Neural Audio and Kinetic Captions (.ass)...")
    audio_path, subs_path = generate_audio(test_script, output_path="drafts/test_voiceover.mp3", subs_path="drafts/test_subs.ass")
    
    print("\n2. Compiling Video via FFmpeg...")
    final_video = compile_video(image_path, audio_path, subs_path, output_path="drafts/test_final_video.mp4")
    
    if final_video:
        print(f"\n✅ Test Complete! Go check out the dynamic video at: {final_video}")

if __name__ == "__main__":
    run_test()
