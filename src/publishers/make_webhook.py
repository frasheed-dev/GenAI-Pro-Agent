import os
import io
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# ─── Image Hosting Config ─────────────────────────────────────────────────────
# IMAGE_HOST options (set in .env or GitHub Secrets):
#   imgbb   → ImgBB API (default, free, works from GitHub Actions cloud IPs)
#   dropbox → Dropbox API (reliable, permanent, requires DROPBOX_ACCESS_TOKEN)
#   catbox  → Catbox.moe (anonymous, zero-config, but blocks cloud/CI IPs — local testing only)
IMAGE_HOST = os.getenv("IMAGE_HOST", "imgbb").lower()


def _convert_to_jpeg(image_path: str) -> io.BytesIO:
    """
    Converts any image file (PNG, etc.) to JPEG in-memory.
    Instagram Graph API strictly requires JPEG format.
    Returns a BytesIO buffer — no temp file written to disk.
    """
    img = Image.open(image_path).convert("RGB")  # PNG has alpha channel; JPEG does not
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85) # Reduced to 85 to save Make.com data quota
    buffer.seek(0)
    return buffer


def _upload_to_catbox(jpeg_buffer: io.BytesIO) -> str:
    """Uploads a JPEG buffer to Catbox.moe and returns a public direct URL.
    WARNING: Catbox blocks cloud/CI provider IPs (GitHub Actions). Use for local testing only.
    """
    print("   📤 Uploading JPEG to Catbox.moe (local testing only)...")
    res = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": ("image.jpg", jpeg_buffer, "image/jpeg")}
    )
    res.raise_for_status()
    url = res.text.strip()
    if not url.startswith("http"):
        raise ValueError(f"Catbox returned unexpected response: {url}")
    return url


def _upload_to_imgbb(jpeg_buffer: io.BytesIO) -> str:
    """
    Uploads a JPEG buffer to ImgBB and returns a public direct image URL.
    ImgBB is a proper image hosting API — works from cloud/CI IPs (GitHub Actions).
    Requires IMGBB_API_KEY in .env / GitHub Secrets.
    Get a free key at: https://api.imgbb.com
    """
    api_key = os.getenv("IMGBB_API_KEY")
    if not api_key:
        raise ValueError("IMGBB_API_KEY is not set in .env or GitHub Secrets")

    import base64
    print("   📤 Uploading JPEG to ImgBB...")
    image_data = base64.b64encode(jpeg_buffer.read()).decode("utf-8")
    res = requests.post(
        "https://api.imgbb.com/1/upload",
        params={"key": api_key},
        data={"image": image_data}
    )
    res.raise_for_status()
    result = res.json()
    if not result.get("success"):
        raise ValueError(f"ImgBB upload failed: {result}")
    # Use display_url — a direct CDN link ending in .jpg, suitable for Instagram
    url = result["data"]["display_url"]
    return url


def _upload_to_dropbox(jpeg_buffer: io.BytesIO) -> str:
    """
    Uploads a JPEG buffer to Dropbox and returns a public direct download URL.
    Requires DROPBOX_ACCESS_TOKEN in .env.
    Files are stored at /GenAI-Pro/instagram_post.jpg (overwritten each run).
    """
    token = os.getenv("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise ValueError("DROPBOX_ACCESS_TOKEN is not set in .env")

    print("   📤 Uploading JPEG to Dropbox...")
    upload_res = requests.post(
        "https://content.dropboxapi.com/2/files/upload",
        headers={
            "Authorization": f"Bearer {token}",
            "Dropbox-API-Arg": '{"path": "/GenAI-Pro/instagram_post.jpg", "mode": "overwrite", "autorename": false}',
            "Content-Type": "application/octet-stream"
        },
        data=jpeg_buffer.read()
    )
    upload_res.raise_for_status()

    # Create (or re-use) a shared link and convert to a direct download URL
    link_res = requests.post(
        "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"path": "/GenAI-Pro/instagram_post.jpg", "settings": {"requested_visibility": "public"}}
    )

    # If link already exists Dropbox returns 409 — fetch the existing one instead
    if link_res.status_code == 409:
        list_res = requests.post(
            "https://api.dropboxapi.com/2/sharing/list_shared_links",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"path": "/GenAI-Pro/instagram_post.jpg", "direct_only": True}
        )
        list_res.raise_for_status()
        shared_url = list_res.json()["links"][0]["url"]
    else:
        link_res.raise_for_status()
        shared_url = link_res.json()["url"]

    # Convert Dropbox share URL to a direct download URL for Instagram Graph API
    # e.g. https://www.dropbox.com/s/xxx/file.jpg?dl=0  →  https://dl.dropboxusercontent.com/s/xxx/file.jpg
    direct_url = shared_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
    return direct_url

def _upload_video_to_dropbox(video_path: str) -> str:
    """
    Uploads an MP4 file to Dropbox and returns a public direct download URL.
    Required for Instagram Reels Graph API.
    Files are stored at /GenAI-Pro/instagram_reel.mp4 (overwritten each run).
    """
    token = os.getenv("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise ValueError("DROPBOX_ACCESS_TOKEN is not set in .env")

    print(f"   📤 Uploading MP4 to Dropbox: {os.path.basename(video_path)}")
    
    with open(video_path, "rb") as f:
        upload_res = requests.post(
            "https://content.dropboxapi.com/2/files/upload",
            headers={
                "Authorization": f"Bearer {token}",
                "Dropbox-API-Arg": '{"path": "/GenAI-Pro/instagram_reel.mp4", "mode": "overwrite", "autorename": false}',
                "Content-Type": "application/octet-stream"
            },
            data=f
        )
    upload_res.raise_for_status()

    # Create (or re-use) a shared link and convert to a direct download URL
    link_res = requests.post(
        "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"path": "/GenAI-Pro/instagram_reel.mp4", "settings": {"requested_visibility": "public"}}
    )

    if link_res.status_code == 409:
        list_res = requests.post(
            "https://api.dropboxapi.com/2/sharing/list_shared_links",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"path": "/GenAI-Pro/instagram_reel.mp4", "direct_only": True}
        )
        list_res.raise_for_status()
        shared_url = list_res.json()["links"][0]["url"]
    else:
        link_res.raise_for_status()
        shared_url = link_res.json()["url"]

    # Convert Dropbox share URL to a direct download URL
    direct_url = shared_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
    return direct_url


def _get_public_image_url(image_path: str) -> str:
    """
    Converts the local PNG image to JPEG and uploads it to the configured host.
    Returns a publicly accessible direct URL for the Instagram Graph API.
    """
    print(f"🌍 Converting PNG → JPEG and uploading via [{IMAGE_HOST.upper()}]...")
    jpeg_buffer = _convert_to_jpeg(image_path)

    if IMAGE_HOST == "imgbb":
        return _upload_to_imgbb(jpeg_buffer)
    elif IMAGE_HOST == "dropbox":
        return _upload_to_dropbox(jpeg_buffer)
    else:
        # catbox — only use for local testing, NOT GitHub Actions (cloud IPs are blocked)
        return _upload_to_catbox(jpeg_buffer)


def post_to_make(platform: str, text: str, image_path: str = None) -> bool:
    """
    Sends the post data (and image file) to a Make.com Webhook.
    Make.com handles the OAuth and native posting to LinkedIn/Facebook/Instagram.

    Instagram flow:
      - Image is converted PNG → JPEG (Instagram Graph API requirement)
      - JPEG is uploaded to Dropbox or Catbox to get a public URL
      - Payload is sent as clean JSON (NOT multipart) so Make.com surfaces image_url
    Facebook/LinkedIn flow:
      - Binary image file is attached as multipart/form-data
    """
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")

    if not webhook_url:
        print("❌ Error: MAKE_WEBHOOK_URL is not defined in .env")
        return False

    print(f"📡 Sending payload to Make.com Webhook for {platform}...")

    data = {
        "platform": platform.lower(),
        "text": text,
        "image_url": ""  # Always present so Make.com's schema always includes this field
    }

    # ── Instagram Reel: public URL required (MP4) ───────────────────────────
    if platform.lower() == "instagram_reel":
        if not image_path or not os.path.exists(image_path) or not image_path.endswith(".mp4"):
            print("❌ Instagram Reels requires an MP4 file. Aborting.")
            return False
        try:
            data["video_url"] = _upload_video_to_dropbox(image_path)
            if not data["video_url"]:
                print("❌ Dropbox upload failed. Aborting.")
                return False
            print(f"✅ Public MP4 URL: {data['video_url']}")
            # Make.com expects the URL in 'image_url' parameter for the generic webhook mapping
            data["image_url"] = data["video_url"]
        except Exception as e:
            print(f"❌ Failed to generate public video URL: {e}")
            return False

    # ── Instagram: public URL required, clean JSON payload ────────────────────
    elif platform.lower() == "instagram":
        if not image_path or not os.path.exists(image_path):
            print("❌ Instagram requires an image but none was found. Aborting.")
            return False
        try:
            data["image_url"] = _get_public_image_url(image_path)
            if not data["image_url"]:
                print("❌ Image host returned an empty URL. Aborting to prevent Make.com validation error.")
                return False
            print(f"✅ Public JPEG URL: {data['image_url']}")
        except Exception as e:
            print(f"❌ Failed to generate public image URL: {e}")
            return False

    # ── Facebook / LinkedIn: binary file upload via multipart ─────────────────
    # Instagram/Instagram Reels are explicitly excluded — sending multipart buries image_url from Make.com's mapper.
    files = None
    jpeg_buffer = None
    if image_path and os.path.exists(image_path) and platform.lower() not in ("instagram", "instagram_reel"):
        # Convert the large PNG to a compressed JPEG in memory to save Make.com data transfer quota
        jpeg_buffer = _convert_to_jpeg(image_path)
        files = {
            "image": ("image.jpg", jpeg_buffer, "image/jpeg")
        }

    try:
        if files:
            response = requests.post(webhook_url, data=data, files=files)
        else:
            # Instagram (and any platform without a file) sends as clean JSON
            response = requests.post(webhook_url, json=data)

        response.raise_for_status()
        print("✅ Successfully triggered Make.com Webhook!")
        return True
    except Exception as e:
        print(f"❌ Failed to send to Make.com: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Response: {response.text}")
        return False
    finally:
        if jpeg_buffer:
            jpeg_buffer.close()
