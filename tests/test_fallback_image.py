"""
test_fallback_image.py
───────────────────────
Validates the final fallback mechanism for news image creation when all AI image
generators (Google Nano Banana, Hugging Face, Pollinations) fail or are unavailable.

Ensures:
  1. generate_fallback_background() creates a 1080x1350 dark-bluish gradient image.
  2. create_news_image(..., force_fallback=True) generates a complete, branded graphic card.
  3. Output file exists, is non-empty, and has valid dimensions (1080x1350).

Usage:
  python tests/test_fallback_image.py
"""

import os
import sys
import io
from PIL import Image

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from core.image_generator import generate_fallback_background, create_news_image

OUTPUT_PATH = "drafts/test_fallback_news_image.png"

def test_fallback_image_generation():
    print("═" * 60)
    print("TESTING PROGRAMMATIC FALLBACK IMAGE GENERATION")
    print("═" * 60)
    
    test_headline = "Meta Hit a Wall on *AI Agents* as Progress Slower Than Expected"
    test_prompt = "Abstract 3D digital network with floating red off switch"

    print("\n1. Testing generate_fallback_background()...")
    fallback_bg = generate_fallback_background(1080, 1350)
    assert fallback_bg is not None, "generate_fallback_background returned None"
    assert fallback_bg.size == (1080, 1350), f"Unexpected size: {fallback_bg.size}"
    print("   ✅ Direct fallback background creation passed.")

    print("\n2. Testing create_news_image() with force_fallback=True...")
    result_path = create_news_image(
        image_prompt=test_prompt,
        headline=test_headline,
        output_path=OUTPUT_PATH,
        force_fallback=True
    )

    assert result_path is not None, "create_news_image returned None"
    assert os.path.exists(result_path), f"Output file does not exist at {result_path}"
    assert os.path.getsize(result_path) > 0, "Generated image file is empty"
    print(f"   ✅ create_news_image fallback path saved to: {result_path}")

    # Inspect generated image details
    with Image.open(result_path) as img:
        assert img.size == (1080, 1350), f"Image size mismatch: {img.size}"
        assert img.mode == "RGB", f"Image mode mismatch: {img.mode}"
        print(f"   ✅ Verified image dimensions: {img.size[0]}x{img.size[1]}, mode: {img.mode}, file size: {os.path.getsize(result_path)/1024:.1f} KB")

    print("\n" + "═" * 60)
    print("ALL FALLBACK IMAGE TESTS PASSED SUCCESSFULLY! 🎉")
    print("═" * 60)

if __name__ == "__main__":
    test_fallback_image_generation()
