"""
Make.com Webhook Schema Training Tool
======================================

Two modes:

  MODE 1 — --retrain (DEFAULT)
    Sends a MULTIPART payload (same format as Facebook/LinkedIn).
    Use this when Make.com's "Re-determine data structure" needs to learn
    the COMPLETE schema: platform + text + image_url + image binary fields.

    WHY: The LinkedIn module needs image.name (→ fileName) and image.data (→ data).
    Those only appear when multipart is sent. Running the Instagram-only JSON test
    previously wiped those fields from the schema — this restores them.

    Run while Make.com webhook is in "Re-determine data structure" mode.

  MODE 2 — --instagram
    Sends a JSON-only payload for the Instagram platform.
    Use this ONLY if you need to verify image_url appears for Instagram in isolation.

HOW TO USE (retrain — most common):
  1. Open Make.com scenario → click Webhook module → "Re-determine data structure" → it waits
  2. Run:  python tests/test_instagram_webhook.py --retrain
  3. Make.com shows the FULL schema:  platform | text | image_url | image.name | image.data | image.mime
  4. Click Save — LinkedIn/Facebook routes still see image.name/image.data, Instagram route sees image_url

HOW TO USE (instagram only):
  1. Open Make.com scenario → click Webhook module → "Re-determine data structure" → it waits
  2. Run:  python tests/test_instagram_webhook.py --instagram
  3. Only use this if you're specifically testing the Instagram route in isolation
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv()

WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
if not WEBHOOK_URL:
    print("❌ MAKE_WEBHOOK_URL not set in .env — aborting.")
    sys.exit(1)

IMAGE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'drafts', 'news_image_universal.png')
)

# ─── Parse mode ──────────────────────────────────────────────────────────────
mode = "--retrain"
if len(sys.argv) > 1:
    mode = sys.argv[1].lower()

print(f"\n{'='*60}")
print(f"  Make.com Schema Training Tool")
print(f"  Mode: {'RETRAIN (multipart — restores LinkedIn/FB fields)' if mode == '--retrain' else 'INSTAGRAM JSON only'}")
print(f"{'='*60}\n")


# ─── MODE 1: RETRAIN — send multipart WITH image_url ─────────────────────────
if mode == "--retrain":
    print("📋 Sending MULTIPART payload to retrain Make.com schema...")
    print("   This will restore: image.name, image.data, image.mime, image_url\n")

    if not os.path.exists(IMAGE_PATH):
        print(f"❌ No image found at: {IMAGE_PATH}")
        print("   Run the agent once in draft mode first to generate the image.")
        print("   Command:  python main.py --platform facebook --draft true")
        sys.exit(1)

    # Send multipart — same format as Facebook/LinkedIn production runs
    # data dict fields become form fields in multipart, so image_url IS included in schema
    data = {
        "platform": "facebook",  # Tells Make.com this is the multipart platform format
        "text": "[SCHEMA RETRAIN] This teaches Make.com the full schema. Not a real post.",
        "image_url": "https://files.catbox.moe/schema_retrain_placeholder.jpg"  # Non-empty so Make.com sees it
    }

    with open(IMAGE_PATH, "rb") as img_file:
        files = {
            "image": (os.path.basename(IMAGE_PATH), img_file, "image/png")
        }
        response = requests.post(WEBHOOK_URL, data=data, files=files)

    print(f"📬 Make.com response: {response.status_code} — {response.text}")

    if response.status_code == 200:
        print("\n✅ SUCCESS! The complete schema has been sent to Make.com.")
        print("\n📌 After clicking 'Save' in Make.com, your schema should now contain:")
        print("   • platform    → used by Router filters")
        print("   • text        → caption/post body")
        print("   • image_url   → Photo URL for Instagram module")
        print("   • image.name  → fileName for LinkedIn module")
        print("   • image.data  → data for LinkedIn module")
        print("   • image.mime  → mime type")
        print("\n⚠️  If LinkedIn module still shows errors, re-map image.name → fileName")
        print("   and image.data → data inside the LinkedIn module settings.")
    else:
        print("\n❌ Webhook returned a non-200 status. Check your MAKE_WEBHOOK_URL.")


# ─── MODE 2: INSTAGRAM JSON only ─────────────────────────────────────────────
elif mode == "--instagram":
    print("📋 Sending JSON payload for Instagram schema test...")

    # Upload image to Catbox for a real URL
    image_url = "https://files.catbox.moe/instagram_test_placeholder.jpg"
    if os.path.exists(IMAGE_PATH):
        print("📤 Uploading image to Catbox.moe...")
        with open(IMAGE_PATH, "rb") as f:
            res = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f}
            )
            if res.status_code == 200 and res.text.strip().startswith("http"):
                image_url = res.text.strip()
                print(f"✅ Public URL: {image_url}")

    payload = {
        "platform": "instagram",
        "text": "[SCHEMA TEST] Instagram JSON payload. Not a real post.",
        "image_url": image_url
    }

    response = requests.post(WEBHOOK_URL, json=payload)
    print(f"📬 Make.com response: {response.status_code} — {response.text}")

    if response.status_code == 200:
        print("\n✅ Instagram JSON schema sent. Make.com now sees: platform | text | image_url")
        print("⚠️  WARNING: This wipes binary fields from schema. Run --retrain afterwards!")
    else:
        print("\n❌ Webhook returned non-200. Check MAKE_WEBHOOK_URL.")

else:
    print(f"❌ Unknown mode: {mode}")
    print("   Usage: python tests/test_instagram_webhook.py [--retrain | --instagram]")
    sys.exit(1)
