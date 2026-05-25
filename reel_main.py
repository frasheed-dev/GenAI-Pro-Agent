import os
import sys
import time
import argparse

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to python path to make importing clean
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.fetcher import fetch_latest_news
from core.llm_processor import curate_articles, draft_reel_script
from core.image_generator import create_slide_image
from core.tts_vibevoice import VibeVoiceEngine
from core.reel_compositor import compile_slide, compile_reel
from publishers.make_webhook import post_to_make
from core.state_manager import mark_as_published

def main(publish=False, speaker_name="Carter"):
    print("=== Starting GenAI Pro Reels Pipeline ===")
    
    # 1. Fetch
    print("\n[Stage 1] Fetching recent AI news feeds...")
    articles = fetch_latest_news(hours_ago=72)
    if not articles:
        print("No articles found.")
        return
        
    # 2. Process
    print(f"\n[Stage 2] Submitting {len(articles)} headlines to Gemini for curation...")
    curated = curate_articles(articles)
    
    if not curated:
        print("No highly relevant GenAI articles found today matching our standards.")
        return
        
    # 3. Draft Script
    print("\n[Stage 3] Drafting Multi-Slide Reel Script...")
    script_data = draft_reel_script(curated)
    if not script_data or "slides" not in script_data:
        print("Failed to draft reel script.")
        return
        
    slides = script_data["slides"]
    total_slides = len(slides)
    print(f"Generated script with {total_slides} slides.")
    
    # 4. Generate Assets and Compile Slides
    print("\n[Stage 4] Generating Assets & Compiling Slides...")
    os.makedirs('drafts/reels', exist_ok=True)
    
    try:
        # Load VibeVoice model once
        tts_engine = VibeVoiceEngine(speaker_name=speaker_name)
    except Exception as e:
        print(f"Failed to initialize VibeVoice: {e}")
        return
        
    slide_videos = []
    
    for i, slide in enumerate(slides):
        idx = i + 1
        print(f"\n--- Processing Slide {idx}/{total_slides} ---")
        print(f"Caption: {slide.get('caption', '')}")
        print(f"Narration: {slide.get('narration', '')}")
        
        image_path = f"drafts/reels/slide_{idx}.png"
        audio_path = f"drafts/reels/slide_{idx}.wav"
        video_path = f"drafts/reels/slide_{idx}.mp4"
        
        # A. Image
        print(f"[{idx}] Generating background image...")
        create_slide_image(
            image_prompt=slide.get("image_prompt", "futuristic AI technology"),
            slide_index=idx,
            total_slides=total_slides,
            output_path=image_path
        )
        
        # B. Audio
        print(f"[{idx}] Generating VibeVoice audio...")
        tts_engine.generate_audio(slide.get("narration", ""), audio_path)
        
        # C. Composite
        print(f"[{idx}] Compositing slide video with sliding text...")
        root_dir = os.path.dirname(__file__)
        font_path = os.path.join(root_dir, "assets", "fonts", "Roboto-Black.ttf")
        
        compile_slide(
            slide_index=idx,
            image_path=image_path,
            audio_path=audio_path,
            caption=slide.get("caption", ""),
            output_path=video_path,
            font_path=font_path
        )
        
        if os.path.exists(video_path):
            slide_videos.append(video_path)
        else:
            print(f"Error: Failed to compile slide {idx}")
            return
            
    # 5. Concat Reel
    print("\n[Stage 5] Concatenating Final Reel...")
    final_output = "drafts/reels/final_reel.mp4"
    compile_reel(slide_videos, final_output)
    
    if not os.path.exists(final_output):
        print("Failed to compile final Reel.")
        return
        
    print(f"\n✅ Reel successfully generated: {final_output}")
    
    # 6. Publish
    if publish:
        print("\n[Stage 6] 🚀 AUTONOMOUS MODE: Publishing to Instagram Reels...")
        
        # We use a summary text for the Instagram caption
        caption_text = "Today's top AI news! 👇\n\n"
        for article in curated:
            caption_text += f"🔹 {article['title']}\n"
        caption_text += "\n#GenAI #ArtificialIntelligence #TechNews #OpenAI"
        
        success = post_to_make("instagram_reel", caption_text, final_output)
        if success:
            print("Successfully published Reel to Instagram!")
            for article in curated:
                mark_as_published(article["link"], "instagram_reel")
        else:
            print("Failed to publish Reel.")
    else:
        print("\n[Stage 6] 🛡️ DRAFT MODE: Reel saved locally. Run with --publish to post to Instagram.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GenAI Pro Reels Generator")
    parser.add_argument("--publish", action="store_true", help="Publish the generated Reel to Instagram")
    parser.add_argument("--speaker", type=str, default="Carter", help="VibeVoice speaker preset (e.g. Carter, Davis)")
    args = parser.parse_args()
    
    main(publish=args.publish, speaker_name=args.speaker)
