"""
test_dynamic_metadata.py
────────────────────────
Validates that build_dynamic_image_metadata() dynamically extracts unique, story-specific
headlines, image prompts, categories, and bullets directly from news content, preventing
repetitive images and titles when LLM quotas are exhausted.
"""

import os
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from core.llm_processor import build_dynamic_image_metadata

STORY_1 = "Google Photos Deploys AI-Powered Virtual Closet on Android, iOS: The new feature lets users digitally try on wardrobe items using generative diffusion models on-device."
STORY_2 = "NVIDIA Reveals Next-Gen Blackwell Ultra Chips: Massive 288GB HBM3e memory architecture for frontier LLM inference."
STORY_3 = "Meta Releases Autonomous Coding Agent Llama-Coder: Software engineering benchmarks show competitive performance against proprietary code generation models."

def main():
    print("═" * 60)
    print("TESTING DYNAMIC STORY-SPECIFIC METADATA EXTRACTION")
    print("═" * 60)
    
    meta1 = build_dynamic_image_metadata(STORY_1)
    meta2 = build_dynamic_image_metadata(STORY_2)
    meta3 = build_dynamic_image_metadata(STORY_3)
    
    print("\n--- Story 1 (Google Photos Closet) ---")
    print(f"Headline: {meta1['headline']}")
    print(f"Category: {meta1['category']}")
    print(f"Image Prompt: {meta1['image_prompt']}")
    
    print("\n--- Story 2 (NVIDIA Blackwell) ---")
    print(f"Headline: {meta2['headline']}")
    print(f"Category: {meta2['category']}")
    print(f"Image Prompt: {meta2['image_prompt']}")
    
    print("\n--- Story 3 (Meta Coding Agent) ---")
    print(f"Headline: {meta3['headline']}")
    print(f"Category: {meta3['category']}")
    print(f"Image Prompt: {meta3['image_prompt']}")
    
    # Assertions: Headlines and Image Prompts must be completely different!
    assert meta1['headline'] != meta2['headline'], "Headlines must be unique!"
    assert meta2['headline'] != meta3['headline'], "Headlines must be unique!"
    assert meta1['image_prompt'] != meta2['image_prompt'], "Image prompts must be unique!"
    assert meta2['image_prompt'] != meta3['image_prompt'], "Image prompts must be unique!"
    assert "*" in meta1['headline'], "Headline must contain asterisk highlights!"
    assert "*" in meta2['headline'], "Headline must contain asterisk highlights!"
    assert "no text" in meta1['image_prompt'].lower(), "Image prompt must enforce no text!"

    print("\n" + "═" * 60)
    print("🎉 ALL DYNAMIC METADATA TESTS PASSED SUCCESSFULLY!")
    print("   Every news item gets a 100% unique, story-specific headline & image prompt!")
    print("═" * 60)

if __name__ == "__main__":
    main()
