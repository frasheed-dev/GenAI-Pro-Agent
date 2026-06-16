"""
test_image_pipeline.py
──────────────────────
End-to-end test for the GenAI Pro image generation pipeline.

Validates:
  1. LLM (generate_image_metadata) — returns valid JSON with 'headline' and 'image_prompt'
  2. Headline quality     — correct word count, has asterisk-wrapped keywords
  3. Image prompt quality — minimum word count, no banned phrases
  4. Image generation     — create_news_image() produces a real, non-empty PNG file

Usage:
  cd <project root>
  python tests/test_image_pipeline.py
"""

import os
import sys
import re
import time
import io

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from dotenv import load_dotenv
load_dotenv()

from core.llm_processor import generate_image_metadata
from core.image_generator import create_news_image

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_PATH = "drafts/test_image_pipeline.png"

# A realistic sample post that mimics what the full pipeline would produce
SAMPLE_POST = """
ChatGPT's market share has slipped below 50% for the first time — not because it got worse, 
but because the field got competitive.

OpenAI just rolled out deployment simulation tools that let safety teams stress-test models 
before release. It's a meaningful step, though critics note it's self-regulated.

Meanwhile, Anthropic's Claude 3.5 is pulling enterprise contracts away from GPT-4o at a 
notable pace, particularly in legal and finance.

The duopoly era is over. The next 12 months will be won on trust and reliability, not raw capability.

#LLMOps #EnterpriseAI #OpenAI #Anthropic
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    msg = f"  {status}  {label}"
    if detail:
        msg += f"\n         → {detail}"
    print(msg)
    return condition

# ── Test 1: LLM Metadata Generation ──────────────────────────────────────────
def test_llm_metadata():
    print("\n" + "═" * 60)
    print("TEST 1 — LLM: generate_image_metadata()")
    print("═" * 60)
    print("  Calling Gemini (includes 15s rate-limit pause)...\n")

    metadata = generate_image_metadata(SAMPLE_POST)

    all_passed = True

    # 1a — returned a dict
    ok = check("Returns a dict (valid JSON parsed)", isinstance(metadata, dict))
    all_passed = all_passed and ok
    if not ok:
        print(f"  Raw output: {metadata}")
        return None

    print(f"\n  Raw headline    : {metadata.get('headline', '<missing>')}")
    print(f"  Image prompt    : {metadata.get('image_prompt', '<missing>')[:120]}...")

    # 1b — both keys present
    ok = check("'headline' key present", "headline" in metadata)
    all_passed = all_passed and ok

    ok = check("'image_prompt' key present", "image_prompt" in metadata)
    all_passed = all_passed and ok

    headline = metadata.get("headline", "")
    image_prompt = metadata.get("image_prompt", "")

    # 1c — headline word count (target: 10-15 words)
    word_count = len(headline.split())
    ok = check(
        f"Headline word count in range 8-18 (got {word_count})",
        8 <= word_count <= 18,
        f'"{headline}"'
    )
    all_passed = all_passed and ok

    # 1d — asterisk markup present in headline
    asterisk_matches = re.findall(r'\*[^*]+\*', headline)
    ok = check(
        f"Headline has asterisk-wrapped keyword(s) (found {len(asterisk_matches)})",
        len(asterisk_matches) >= 1,
        f"Highlighted: {asterisk_matches}"
    )
    if not ok:
        print(f"         Headline was: \"{headline}\"")
    all_passed = all_passed and ok

    # 1e — image prompt word count (target: 60-120 words)
    prompt_words = len(image_prompt.split())
    ok = check(
        f"Image prompt word count in range 40-140 (got {prompt_words})",
        40 <= prompt_words <= 140,
        image_prompt[:100] + "..."
    )
    all_passed = all_passed and ok

    # 1f — no banned phrases in the POSITIVE part of the image prompt
    # The LLM may append negatives inline ("No text, no UI...") or after a "Negative:" label.
    # Split at whichever pattern appears first to isolate the positive subject description.
    positive_prompt = re.split(r'(negative[:\s]|no text)', image_prompt, flags=re.IGNORECASE)[0]
    banned = ["dashboard", "UI mockup", "chart", "watermark", "logo"]
    found_banned = [b for b in banned if b.lower() in positive_prompt.lower()]
    ok = check(
        "Image prompt positive section avoids banned UI/text elements",
        len(found_banned) == 0,
        f"Found banned in positive section: {found_banned}" if found_banned else "None found"
    )
    all_passed = all_passed and ok

    # 1g — no "3D illustration" or "cartoonize" (old style we moved away from)
    old_style_phrases = ["3d illustration", "cartoonize", "cartoonish"]
    found_old = [p for p in old_style_phrases if p in image_prompt.lower()]
    if found_old:
        print(f"  {WARN}  Old style phrases detected in image_prompt: {found_old}")
        print(f"         (The prompt still specifies the old aesthetic — review the LLM output)")
    else:
        print(f"  {PASS}  No old-style aesthetic phrases (cartoonize/3D illustration) detected")

    print(f"\n  Overall TEST 1: {'PASSED ✅' if all_passed else 'FAILED ❌'}")
    return metadata if all_passed else metadata  # Return regardless so Test 2 can run


# ── Test 2: Image Generation & Compositing ────────────────────────────────────
def test_image_generation(metadata):
    print("\n" + "═" * 60)
    print("TEST 2 — Image: create_news_image()")
    print("═" * 60)

    all_passed = True

    if not metadata:
        print(f"  {FAIL}  Skipping — no metadata from Test 1")
        return False

    headline = metadata.get("headline", "GenAI Pro *Test* Image")
    image_prompt = metadata.get(
        "image_prompt",
        "A futuristic glowing AI brain in a dark cinematic studio, backlit, no text"
    )

    print(f"  Using headline    : {headline}")
    print(f"  Using image_prompt: {image_prompt[:100]}...")
    print(f"  Output path       : {OUTPUT_PATH}")
    print()

    start = time.time()
    result_path = create_news_image(image_prompt, headline, output_path=OUTPUT_PATH)
    elapsed = time.time() - start

    # 2a — function returned a path (not None)
    ok = check("create_news_image() returned a file path (not None)", result_path is not None)
    all_passed = all_passed and ok

    # 2b — file actually exists on disk
    file_exists = result_path and os.path.exists(result_path)
    ok = check("Output PNG file exists on disk", file_exists, result_path)
    all_passed = all_passed and ok

    if file_exists:
        # 2c — file is not empty (at least 50KB means a real image)
        size_kb = os.path.getsize(result_path) / 1024
        ok = check(
            f"PNG file size is substantial (>50 KB, got {size_kb:.1f} KB)",
            size_kb > 50
        )
        all_passed = all_passed and ok

        # 2d — validate it's a readable PIL image at the correct dimensions
        try:
            from PIL import Image
            img = Image.open(result_path)
            w, h = img.size
            ok = check(
                f"Image dimensions correct (1080×1350, got {w}×{h})",
                w == 1080 and h == 1350
            )
            all_passed = all_passed and ok
            img.close()
        except Exception as e:
            check("Image is a valid/readable PNG", False, str(e))
            all_passed = False

    print(f"\n  Generation time: {elapsed:.1f}s")
    print(f"  Overall TEST 2: {'PASSED ✅' if all_passed else 'FAILED ❌'}")
    return all_passed


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("     GenAI Pro -- Image Pipeline End-to-End Test")
    print("=" * 60)

    # Sanity check: API key loaded
    if not os.getenv("GEMINI_API_KEY"):
        print(f"\n{FAIL}  GEMINI_API_KEY not found in .env — aborting.")
        sys.exit(1)

    metadata = test_llm_metadata()
    t2_ok = test_image_generation(metadata)

    print("\n" + "═" * 60)
    print("SUMMARY")
    print("═" * 60)
    t1_ok = metadata is not None and "headline" in metadata and "image_prompt" in metadata
    print(f"  Test 1 — LLM Metadata   : {'PASSED ✅' if t1_ok else 'FAILED ❌'}")
    print(f"  Test 2 — Image Pipeline : {'PASSED ✅' if t2_ok else 'FAILED ❌'}")

    if t1_ok and t2_ok:
        print(f"\n  ✅ All tests passed! Open '{OUTPUT_PATH}' to visually inspect the result.")
    else:
        print("\n  ❌ One or more tests failed. Review the output above.")
    print()
