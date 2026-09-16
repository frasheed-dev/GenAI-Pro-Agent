import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to python path to make importing clean
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.config import AUTONOMOUS_MODE
from core.fetcher import fetch_latest_news
from core.llm_processor import curate_articles, draft_social_post, generate_image_metadata
from core.image_generator import create_news_image, create_carousel_deck
from core.video_generator import draft_video_script, generate_audio, compile_video
from publishers.make_webhook import post_to_make
from core.state_manager import mark_as_published
import time
import argparse

def main(selected_platforms=None, is_autonomous=AUTONOMOUS_MODE):
    print("=== Starting GenAI News Agent ===")
    
    # 1. Fetch
    print("\n[Stage 1] Fetching recent AI news feeds...")
    articles = fetch_latest_news(hours_ago=72)
    print(f"Found {len(articles)} total articles across all feeds.")
    
    # 2. Curate
    print("\n[Stage 2] Curating top Generative AI developments...")
    curated = curate_articles(articles)
    
    if not curated:
        print("No highly relevant GenAI articles found today matching our standards.")
        return
        
    # --- NEW: Generate Global Image & Carousel Deck ---
    print("\n[Stage 3] Generating universal news image & 3-slide Carousel Deck...")
    image_path = None
    carousel_paths = []
    
    # We ask Gemini to generate metadata based purely on the raw curated news facts
    news_summary = ""
    for idx, article in enumerate(curated):
        news_summary += f"{idx+1}. {article['title']}: {article['summary']}\n"
        
    metadata = generate_image_metadata(news_summary)
    
    if metadata and "image_prompt" in metadata and "headline" in metadata:
        image_path = create_news_image(
            image_prompt=metadata["image_prompt"], 
            headline=metadata["headline"], 
            output_path="drafts/news_image_universal.png"
        )
        
        # Generate 3-slide Carousel Deck
        carousel_paths = create_carousel_deck(metadata, output_dir="drafts")
        print(f"✅ Generated Carousel Deck: {len(carousel_paths)} slides ready in drafts/")
        
        if image_path:
            image_path = os.path.abspath(image_path)
            
            # --- NEW: Generate Video ---
            # Temporarily paused so we can focus on getting the image-based agent flawlessly posting!
            # To re-enable, add GENERATE_VIDEO=True to your .env file
            if os.getenv("GENERATE_VIDEO", "False").lower() == "true":
                print("\n[Stage 3.5] Generating Short-Form Video...")
                video_script = draft_video_script(curated)
                if video_script:
                    print(f"[Video Script] {video_script}")
                    audio_path, subs_path = generate_audio(video_script, output_path="drafts/voiceover.mp3", subs_path="drafts/subs.ass")
                    video_path = compile_video(image_path, audio_path, subs_path, output_path="drafts/final_video.mp4")
                    if video_path:
                        print(f"✅ Video Asset Ready: {video_path}")
                else:
                    print("Failed to draft video script.")
            else:
                print("\n[Stage 3.5] Video generation is paused (GENERATE_VIDEO=False). Skipping to posting...")
        else:
            print("\n❌ CRITICAL ERROR: Image generation via pollinations.ai failed (create_news_image returned None).")
            print("Aborting the entire process to prevent sending incomplete payloads to Make.com.")
            sys.exit(1)
                
    else:
        print("\n❌ CRITICAL ERROR: Failed to generate universal image metadata from Gemini. Aborting to prevent Make.com errors (scenario requires image).")
        sys.exit(1)
    
    # --- Platform Posting Loop ---
    platforms = selected_platforms if selected_platforms else ["Facebook", "LinkedIn"]
    
    for platform in platforms:
        print(f"\n[Stage 4] Pausing for 15 seconds to respect Gemini Free Tier rate limits...")
        time.sleep(15)
        
        print(f"\n[Stage 4] Drafting {platform} post text...")
        post_content = draft_social_post(platform, curated)
        
        # Check if generation actually succeeded
        if not post_content or "Error generation failed" in post_content:
            print(f"\n❌ CRITICAL ERROR: Post preparation failed for {platform} (LLM drafting issue).")
            print(f"Aborting the entire process to prevent sending incomplete payloads to Make.com. Reason: {post_content}")
            sys.exit(1)
        
        # 5. Publish / Draft Mode
        if is_autonomous:
            print(f"\n[Stage 5] 🚀 AUTONOMOUS MODE: Pushing to Make.com Webhook for {platform}...")
            
            # Use the unified Make.com Webhook Bridge
            success = post_to_make(platform=platform, text=post_content, image_path=image_path)
            
            if success:
                print(f"Post payload successfully handed off to Make.com for {platform}!")
                for article in curated:
                    mark_as_published(article["link"], platform.lower())
            else:
                print(f"\n❌ CRITICAL ERROR: Make.com Webhook failed to process or upload image for {platform}.")
                print("Aborting further platform posting to prevent cascading scenario crashes.")
                sys.exit(1)
                
        else:
            print(f"\n[Stage 5] 🛡️ APPROVAL MODE: Saving draft locally for {platform}...")
            os.makedirs('drafts', exist_ok=True)
            draft_path = f"drafts/post_draft_{platform.lower()}.txt"
            with open(draft_path, "w", encoding="utf-8") as f:
                f.write(post_content)
                
            print(f"\n[Draft Created] Your proposed {platform} post was written to: {draft_path}")
            if image_path:
                print(f"[Image Attached] Universal visual asset: {image_path}")
                
            print(f"\n--- {platform.upper()} DRAFT PREVIEW ---\n")
            print(post_content)
            print("\n---------------------\n")
            print(f"If you approve this, you can manually copy/paste it to {platform}!")
    
    print("\nTo allow me to post automatically next time, set AUTONOMOUS_MODE=True in your .env file.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GenAI Pro Agent")
    parser.add_argument("--platform", type=str, choices=["facebook", "linkedin", "instagram", "x", "all"], default="all", help="Platform to post to")
    parser.add_argument("--draft", type=str, choices=["true", "false"], help="Run in draft mode (True) or autonomous mode (False)")
    args = parser.parse_args()
    
    # Parse platforms
    selected_platforms = ["Facebook", "LinkedIn"]
    if args.platform.lower() == "facebook":
        selected_platforms = ["Facebook"]
    elif args.platform.lower() == "linkedin":
        selected_platforms = ["LinkedIn"]
    elif args.platform.lower() == "instagram":
        selected_platforms = ["Instagram"]
    elif args.platform.lower() == "x":
        selected_platforms = ["X"]
        
    # Parse autonomous mode
    is_autonomous = AUTONOMOUS_MODE
    if args.draft:
        if args.draft.lower() == "true":
            is_autonomous = False
        elif args.draft.lower() == "false":
            is_autonomous = True
            
    main(selected_platforms, is_autonomous)
