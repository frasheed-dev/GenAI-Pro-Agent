import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from core.llm_processor import draft_social_post, generate_image_metadata
from core.image_generator import create_news_image

def run_sandbox():
    print("=== GenAI Pro - Safe Local Sandbox Test ===")
    
    # 1. Mock Data: Completely bypasses RSS feeds and state_manager so nothing is touched
    sample_articles = [
        {
            "title": "Anthropic releases Claude 4 with native coding abilities", 
            "link": "http://example.com/claude", 
            "source": "AI Tech Daily", 
            "summary": "Anthropic has just announced Claude 4, a major leap in language models capable of natively executing code and writing entire applications autonomously.", 
            "published_at": "2026-05-15"
        },
        {
            "title": "Meta's LLaMA-4 open-sourced globally", 
            "link": "http://example.com/llama", 
            "source": "Open Source AI", 
            "summary": "Meta disrupts the AI landscape by releasing their most powerful LLaMA-4 model under a fully permissive open-source license, threatening proprietary models.", 
            "published_at": "2026-05-15"
        }
    ]
    
    # 2. Test the new 3-Part Influencer Prompt
    print("\n[Stage 1] Drafting LinkedIn post text (Testing new 3-part layout)...")
    post_content = draft_social_post("linkedin", sample_articles)
    
    print("\n--- 📝 SANDBOX POST PREVIEW ---\n")
    print(post_content)
    print("\n--------------------------\n")
    
    # 3. Test the Image Generation & Visual Branding
    print("\n[Stage 2] Generating image metadata...")
    metadata = generate_image_metadata(post_content)
    
    if metadata and "image_prompt" in metadata and "headline" in metadata:
        print(f"\n[Stage 3] Synthesizing image with headline: {metadata['headline']}")
        image_path = create_news_image(
            image_prompt=metadata["image_prompt"], 
            headline=metadata["headline"], 
            output_path="drafts/sandbox_image.png"
        )
        if image_path:
            print(f"\n✅ Sandbox test complete! Check your drafts folder for 'sandbox_image.png'")
    else:
        print("❌ Failed to generate image metadata.")

if __name__ == "__main__":
    run_sandbox()
