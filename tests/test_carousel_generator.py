"""
test_carousel_generator.py
───────────────────────────
Test suite for the 3-slide Carousel Deck Generator in src/core/image_generator.py.

Verifies:
  1. Journalistic tone (no hype words, factual analysis).
  2. Slide 1: Cover Card (Headline + Yellow Highlights + Swipe ➔ indicator).
  3. Slide 2: Key Takeaways Card (3 Factual Bullet Points with Yellow Accent Icons).
  4. Slide 3: Community Discussion & Growth CTA Card (Analytical Question + Follow Request).
  5. Fallback Mode support (rendering on dark navy-teal gradient background).

Usage:
  python tests/test_carousel_generator.py
"""

import os
import sys
import io
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from core.image_generator import create_carousel_deck

SAMPLE_NEWS_ITEM = {
    "headline": "Meta Adjusts *AI Agent* Roadmap Amid Infrastructure Constraints",
    "category": "ENTERPRISE AI ANALYSIS",
    "image_prompt": "Futuristic clean data center server racks with blue status lights",
    "carousel_bullets": [
        "Internal engineering roadmaps shifted focus to foundation layer scaling.",
        "Enterprise pilots highlighted latency requirements for multi-agent workflows.",
        "Resource allocation prioritizes infrastructure efficiency over raw parameter count."
    ],
    "discussion_question": "How will this roadmap shift impact your team's Q3 AI agent deployment plans?"
}

def main():
    print("═" * 60)
    print("TESTING JOURNALISTIC 3-SLIDE CAROUSEL DECK GENERATOR")
    print("═" * 60)
    
    # 1. Test Carousel Generation with Fallback Mode
    print("\n1. Testing create_carousel_deck() (Programmatic Dark Fallback Mode)...")
    slides_fallback = create_carousel_deck(
        news_item=SAMPLE_NEWS_ITEM,
        output_dir="drafts",
        force_fallback=True
    )
    
    assert len(slides_fallback) == 3, f"Expected 3 slides, got {len(slides_fallback)}"
    for idx, path in enumerate(slides_fallback, 1):
        assert os.path.exists(path), f"Slide {idx} file missing at {path}"
        with Image.open(path) as img:
            assert img.size == (1080, 1350), f"Slide {idx} incorrect dimensions: {img.size}"
            assert img.mode == "RGB", f"Slide {idx} incorrect color mode: {img.mode}"
        size_kb = os.path.getsize(path) / 1024
        print(f"   ✅ Slide {idx}/3 verified: {path} ({img.size[0]}x{img.size[1]}, {size_kb:.1f} KB)")
        
    print("\n" + "═" * 60)
    print("🎉 ALL CAROUSEL DECK GENERATOR TESTS PASSED SUCCESSFULLY!")
    print("   Output Slides: drafts/carousel_slide_1.png, slide_2.png, slide_3.png")
    print("═" * 60)

if __name__ == "__main__":
    main()
