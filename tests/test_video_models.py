import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
test_video_models.py
====================
Tests pollinations.ai image-to-video generation across all available models.

For each model:
  - Sends our sample background image as a start_frame
  - Measures response time
  - Saves the output video to tests/video_outputs/<model_name>.mp4
  - Prints a timing and quality summary at the end

Usage:
  # Test only the FREE model (ltx-2) — no API key needed:
  python tests/test_video_models.py

  # Test ALL models (paid + free) — requires POLLINATIONS_API_KEY in .env:
  python tests/test_video_models.py --all

  # Test specific models:
  python tests/test_video_models.py --models ltx-2 wan-fast seedance-pro

  # Use a specific background image:
  python tests/test_video_models.py --image drafts/news_image_universal.png

Requirements:
  pip install requests pillow python-dotenv
"""

import os
import sys
import time
import argparse
import requests
import base64
from io import BytesIO
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# ─── Model Registry ───────────────────────────────────────────────────────────
# All image-to-video models available on pollinations.ai as of 2026-05-24
# Source: https://gen.pollinations.ai/image/models

VIDEO_MODELS = {
    # ─── FREE (no API key required) ────────────────────────────────────────────
    "ltx-2": {
        "description": "LTX-2.3 — Fast text/image-to-video with upscaler",
        "resolution": "720P (upscaled)",
        "cost_per_sec": "FREE",
        "paid_only": False,
        "default_duration": 5,
    },

    # ─── PAID (require POLLINATIONS_API_KEY) ───────────────────────────────────
    "wan-fast": {
        "description": "Wan 2.2 — Fast & cheap text/image-to-video",
        "resolution": "480P",
        "cost_per_sec": "0.015 pollen",
        "paid_only": True,
        "default_duration": 5,
    },
    "seedance-pro": {
        "description": "Seedance Pro-Fast — 720p, better prompt adherence",
        "resolution": "720P",
        "cost_per_sec": "0.0375 pollen",
        "paid_only": True,
        "default_duration": 5,
    },
    "wan": {
        "description": "Wan 2.6 — Alibaba text/image-to-video (up to 1080P, 2-15s)",
        "resolution": "1080P",
        "cost_per_sec": "0.075 pollen",
        "paid_only": True,
        "default_duration": 6,
    },
    "grok-video-pro": {
        "description": "Grok Video Pro — xAI official video generation (720p, 1-15s)",
        "resolution": "720P",
        "cost_per_sec": "0.075 pollen",
        "paid_only": True,
        "default_duration": 5,
    },
    "nova-reel": {
        "description": "Nova Reel — Amazon Nova video generation (6-120s, 720p)",
        "resolution": "720P",
        "cost_per_sec": "0.08 pollen",
        "paid_only": True,
        "default_duration": 6,
    },
    "veo": {
        "description": "Veo 3.1 Fast — Google text-to-video with audio (preview)",
        "resolution": "1080P",
        "cost_per_sec": "0.15 pollen",
        "paid_only": True,
        "default_duration": 5,
    },
}

BASE_URL = "https://gen.pollinations.ai"
OUTPUT_DIR = Path("tests/video_outputs")

# Prompt used for all image-to-video calls
# Describes subtle, professional motion — no dramatic changes that would distort branding
VIDEO_PROMPT = (
    "Subtle ambient motion. "
    "Slow gentle camera pull-back. "
    "Atmospheric particle dust floating in light beams. "
    "Cinematic depth of field. "
    "Professional broadcast quality. "
    "No scene cuts. No text generation. No faces."
)


def get_pollinations_image_url(image_path: str = None) -> str:
    """
    Gets a public pollinations.ai image URL to use as the video start_frame.
    Strategy: generate a fresh background image via pollinations.ai image API
    and return its URL directly (already public, no upload needed).
    """
    from urllib.parse import quote

    # Use our standard slide background prompt
    bg_prompt = (
        "futuristic AI neural network visualization, deep blue and gold light beams, "
        "cinematic atmosphere, abstract technology, no text, no faces, 4K quality"
    )
    print(f"   Generating fresh background image via pollinations.ai (gets a public URL)...")
    image_url = (
        f"https://image.pollinations.ai/prompt/{quote(bg_prompt)}"
        f"?width=1080&height=1920&nologo=true&model=flux"
    )
    print(f"   Image URL: {image_url[:90]}...")
    return image_url


def generate_video(model_name: str, image_data_url: str, api_key: str = None) -> tuple:
    """
    Calls the pollinations.ai video endpoint for a given model.
    Uses GET /video/{prompt} with query params as documented.
    Returns (video_bytes, elapsed_seconds) or (None, elapsed_seconds) on failure.
    """
    model_info = VIDEO_MODELS[model_name]
    duration = model_info["default_duration"]

    headers = {"Accept": "video/mp4, */*"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    from urllib.parse import quote
    encoded_prompt = quote(VIDEO_PROMPT, safe="")
    url = f"{BASE_URL}/video/{encoded_prompt}"

    params = {
        "model": model_name,
        "duration": duration,
        "aspectRatio": "9:16",
        "image": image_data_url,
    }
    if api_key:
        params["key"] = api_key

    print(f"   Calling GET /video/{{prompt}}?model={model_name}&duration={duration}s&aspect=9:16...")

    start = time.time()
    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=300,
        )
        elapsed = time.time() - start

        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            video_bytes = response.content
            print(f"   Response: {len(video_bytes) / 1024:.1f} KB  Content-Type: {content_type}  Time: {elapsed:.1f}s")
            return video_bytes, elapsed
        elif response.status_code == 401:
            print(f"   401 Unauthorized — API key required for {model_name}")
            return None, elapsed
        elif response.status_code == 402:
            print(f"   402 Insufficient pollen — top up at enter.pollinations.ai")
            return None, elapsed
        else:
            print(f"   HTTP {response.status_code}: {response.text[:400]}")
            return None, elapsed

    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"   TIMEOUT after {elapsed:.0f}s — model may be overloaded")
        return None, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"   Error: {e}")
        return None, elapsed


def run_tests(models_to_test: list[str], image_path: str, api_key: str = None):
    """Runs video generation tests for all specified models."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  pollinations.ai Video Model Test")
    print(f"  Background image: {image_path}")
    print(f"  API key: {'✅ Set' if api_key else '❌ Not set (free models only)'}")
    print(f"  Models to test: {', '.join(models_to_test)}")
    print(f"{'='*60}\n")

    # Step 1: Get a public image URL to use as start_frame for all models
    try:
        image_url = get_pollinations_image_url(image_path)
    except Exception as e:
        print(f"\nFATAL: Could not get image URL: {e}")
        sys.exit(1)

    print()

    # Step 2: Test each model
    results = []
    for model_name in models_to_test:
        model_info = VIDEO_MODELS[model_name]
        print(f"\n{'─'*60}")
        print(f"  MODEL: {model_name}")
        print(f"  {model_info['description']}")
        print(f"  Resolution: {model_info['resolution']} | Cost: {model_info['cost_per_sec']}")

        if model_info["paid_only"] and not api_key:
            print(f"  ⚠️  SKIPPED — requires POLLINATIONS_API_KEY (paid model)")
            results.append({
                "model": model_name,
                "status": "skipped",
                "elapsed": 0,
                "file_size_kb": 0,
                "output_path": None,
            })
            continue

        video_bytes, elapsed = generate_video(model_name, image_url, api_key)

        if video_bytes:
            output_path = OUTPUT_DIR / f"{model_name}.mp4"
            with open(output_path, "wb") as f:
                f.write(video_bytes)
            file_size_kb = len(video_bytes) / 1024
            print(f"   💾 Saved: {output_path} ({file_size_kb:.0f} KB)")
            results.append({
                "model": model_name,
                "status": "success",
                "elapsed": elapsed,
                "file_size_kb": file_size_kb,
                "output_path": str(output_path),
            })
        else:
            results.append({
                "model": model_name,
                "status": "failed",
                "elapsed": elapsed,
                "file_size_kb": 0,
                "output_path": None,
            })

    # Step 3: Print summary
    print(f"\n\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Model':<20} {'Status':<10} {'Time':>8} {'Size':>10}  Output")
    print(f"  {'─'*20} {'─'*10} {'─'*8} {'─'*10}  {'─'*30}")

    for r in results:
        status_icon = {"success": "✅", "failed": "❌", "skipped": "⚠️ "}.get(r["status"], "?")
        time_str = f"{r['elapsed']:.1f}s" if r["elapsed"] > 0 else "—"
        size_str = f"{r['file_size_kb']:.0f} KB" if r["file_size_kb"] > 0 else "—"
        output_str = r["output_path"] or "—"
        print(f"  {r['model']:<20} {status_icon} {r['status']:<8} {time_str:>8} {size_str:>10}  {output_str}")

    successes = [r for r in results if r["status"] == "success"]
    if successes:
        print(f"\n  ✅ {len(successes)} video(s) saved to: {OUTPUT_DIR.absolute()}")
        print(f"  👁️  Open them in VLC or your video player to compare quality.")
    else:
        print(f"\n  No videos generated successfully.")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Test pollinations.ai image-to-video models for GenAI Pro Reels pipeline"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all models (paid + free). Requires POLLINATIONS_API_KEY in .env",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=list(VIDEO_MODELS.keys()),
        help="Specific models to test (space-separated)",
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Path to background image (PNG/JPG). Default: auto-generate a sample.",
    )
    args = parser.parse_args()

    api_key = os.getenv("POLLINATIONS_API_KEY")

    # Determine which models to test
    if args.models:
        models_to_test = args.models
    elif args.all:
        models_to_test = list(VIDEO_MODELS.keys())
    else:
        # Default: only free models
        models_to_test = [m for m, info in VIDEO_MODELS.items() if not info["paid_only"]]
        print(f"ℹ️  No --all flag set. Testing free models only: {models_to_test}")
        print(f"   To test paid models too, set POLLINATIONS_API_KEY and run with --all\n")

    # Determine background image
    image_path = args.image

    if not image_path:
        # Try to find an existing generated image from the drafts folder
        candidates = [
            "drafts/news_image_universal.png",
            "drafts/test_slide_background.png",
        ]
        for c in candidates:
            if os.path.exists(c):
                image_path = c
                print(f"ℹ️  Using existing image: {image_path}")
                break

    if not image_path or not os.path.exists(image_path):
        # Auto-generate a simple test background via pollinations.ai image
        print("ℹ️  No background image found. Generating a sample from pollinations.ai...")
        os.makedirs("drafts", exist_ok=True)
        image_path = "drafts/test_slide_background.png"
        sample_prompt = (
            "futuristic AI data center, glowing blue servers, cinematic lighting, "
            "dark background, abstract technology, no text, no people, 4K quality"
        )
        from urllib.parse import quote
        img_url = f"https://image.pollinations.ai/prompt/{quote(sample_prompt)}?width=1080&height=1920&nologo=true"
        print(f"   Fetching: {img_url[:80]}...")
        img_response = requests.get(img_url, timeout=60)
        if img_response.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(img_response.content)
            print(f"   ✅ Sample background saved: {image_path}")
        else:
            print(f"   ❌ Failed to generate background: HTTP {img_response.status_code}")
            sys.exit(1)

    run_tests(models_to_test, image_path, api_key)


if __name__ == "__main__":
    main()
