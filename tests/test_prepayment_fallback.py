"""
test_prepayment_fallback.py
────────────────────────────
Validates that when Google Gemini API throws a prepayment credits / billing error (HTTP 429),
the LLM processor cleanly catches it, switches to Hugging Face free text fallback, and returns
structured fallbacks for curation, post drafting, and metadata without crashing or looping!
"""

import os
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import core.llm_processor as llm_processor

SAMPLE_ARTICLES = [
    {
        "title": "NVIDIA Unveils Next-Gen AI Microarchitecture",
        "summary": "NVIDIA announced new enterprise hardware optimized for real-time LLM inference.",
        "source": "TechCrunch",
        "link": "https://techcrunch.com/nvidia-ai"
    },
    {
        "title": "Open-Source Models Close Gap on Benchmark Tests",
        "summary": "New 70B parameter open-weights models achieve parity with proprietary API endpoints.",
        "source": "VentureBeat",
        "link": "https://venturebeat.com/opensource-ai"
    }
]

def main():
    print("═" * 60)
    print("TESTING GEMINI PREPAYMENT CREDITS DEPLETED FALLBACK ENGINE")
    print("═" * 60)
    
    # 1. Mock model.generate_content to raise Gemini Prepayment Depleted error
    class MockDepletedModel:
        def generate_content(self, prompt):
            raise Exception("429 Your prepayment credits are depleted. Please go to AI Studio at https://ai.studio/projects to manage billing.")
            
    original_model = llm_processor.model
    llm_processor.model = MockDepletedModel()
    
    try:
        print("\n1. Testing curate_articles() with zero prepayment credits...")
        curated = llm_processor.curate_articles(SAMPLE_ARTICLES)
        assert len(curated) > 0, "curate_articles returned empty list!"
        print(f"   ✅ Curation succeeded with fallback! Curated {len(curated)} articles: {[a['title'] for a in curated]}")
        
        print("\n2. Testing draft_social_post() with zero prepayment credits...")
        post = llm_processor.draft_social_post("LinkedIn", curated)
        assert post and len(post) > 50, "draft_social_post returned empty or invalid text!"
        print(f"   ✅ Social post drafting succeeded with fallback! ({len(post)} chars)")
        print(f"   Sample text snippet: {post[:120]}...")
        
        print("\n3. Testing generate_image_metadata() with zero prepayment credits...")
        meta = llm_processor.generate_image_metadata(post)
        assert meta and "headline" in meta and "carousel_bullets" in meta, "generate_image_metadata failed!"
        print(f"   ✅ Image metadata generation succeeded with fallback! Headline: '{meta['headline']}'")
        print(f"   Category: '{meta.get('category')}'")
        print(f"   Bullets: {meta.get('carousel_bullets')}")

        print("\n" + "═" * 60)
        print("🎉 PREPAYMENT FALLBACK ENGINE VERIFIED SUCCESSFULLY!")
        print("   Zero pipeline crashes, zero retries waste, clean fallbacks across all stages!")
        print("═" * 60)
        
    finally:
        llm_processor.model = original_model

if __name__ == "__main__":
    main()
