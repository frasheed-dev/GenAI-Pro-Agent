# Gen AI Pro: Instagram Integration Architecture

This document serves as the historical context and architecture decisions for the Instagram posting pipeline.

## 1. The Instagram API Limitation
Unlike Facebook and LinkedIn, the official Instagram Graph API (and by extension, Make.com's Instagram for Business module) **strictly refuses direct binary file uploads**. 
- It requires a public, web-accessible URL (`image_url`) to fetch the photo.
- The image must be in **JPEG format** — PNG is rejected by the API.
- Standard cloud storage providers (like Google Drive) often block automated third-party scraping via "restricted scopes," rendering them unreliable for Make.com.

## 2. The Python Solution: PNG → JPEG Conversion + Public URL
The Python engine handles both format conversion and public URL generation autonomously.
- **File:** `src/publishers/make_webhook.py`
- **JPEG Conversion:** Before uploading, the engine converts `news_image_universal.png` → JPEG in-memory using Pillow (`Image.convert("RGB")` removes the alpha channel, `Image.save(..., format="JPEG")` encodes it). No temp file is written to disk.
- **Public Hosting:** The JPEG buffer is uploaded to the configured image host (see Section 3).
- **Webhook Payload:** The returned direct URL is injected as `image_url` in the Make.com JSON payload.

## 3. Image Hosting: Catbox (Testing) vs Dropbox (Production)
Controlled by the `IMAGE_HOST` variable in `.env`:

| Setting | Host | Use Case |
|---|---|---|
| `IMAGE_HOST=catbox` | Catbox.moe (anonymous CDN) | Testing — zero config, no credentials |
| `IMAGE_HOST=dropbox` | Dropbox API | Production — reliable, permanent, owned |

**Dropbox setup:** Generate a Dropbox API token and add it to `.env` as `DROPBOX_ACCESS_TOKEN`. Files are stored at `/GenAI-Pro/instagram_post.jpg` and overwritten each run. The share URL is automatically converted to a `dl.dropboxusercontent.com` direct link required by Instagram.

## 4. The image_url Visibility Fix (Make.com Schema Bug)
**Problem:** Make.com's webhook module was learning the data schema from Facebook/LinkedIn runs, which sent `multipart/form-data` (binary file upload). In multipart payloads, Make.com buries form fields and they don't appear in the module's field mapper — so `image_url` was invisible.

**Fix:** Instagram is explicitly excluded from the binary `files` block in `make_webhook.py`. It sends a **clean JSON payload** only:
```json
{ "platform": "instagram", "text": "...", "image_url": "https://..." }
```
This makes `image_url` fully visible in Make.com's schema and mappable to the Instagram module's `Photo URL` field.

**To reteach Make.com the schema** after this fix, run:
```bash
python tests/test_instagram_webhook.py
```
While Make.com's webhook module is in "Re-determine data structure" mode. Then map `image_url` → `Photo URL`.

## 5. LLM Drafting Adjustments
- **File:** `src/core/llm_processor.py`
- **Instructions:** Instagram captions do not support clickable URLs. The LLM prompt explicitly instructs the model to omit raw URLs and use "Link in Bio" phrasing for Instagram drafts. It also encourages heavier emoji usage and vertical spacing.
