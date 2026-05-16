# GENAI_PRO - Project Context (Updated May 2026)

## Project Goal
GenAI Pro has evolved from a technical scripting project into an active **Media-to-SaaS Business Venture**. 

Our strategic funnel is:
1. **Automated Media:** Use our "Zero-Cost Content Engine" to autonomously publish high-signal Generative AI news to social media platforms (Facebook, LinkedIn, Instagram) to farm organic impressions.
2. **Audience Capture:** Funnel social traffic to our owned web property (`genai-pro.com`) to build a highly lucrative B2B newsletter.
3. **Monetization:** Generate revenue through high-ticket newsletter sponsorships, affiliate marketing, and eventually productizing the Agent architecture itself as a B2B SaaS offering.

*(For detailed timelines, see `.docs/business_plan_2026.md`)*

## Current State (What is completed)
- **Core Architecture Built:** A modular system located in `src/core` that fetches RSS feeds (OpenAI, Anthropic, Google) and curates them.
- **The Gemma 3 LLM Brain:** We utilize the Developer API to access `gemma-3-27b-it`, Google's highly capable open-weights model. We explicitly shifted to this model to bypass the strict daily rate limits placed on Gemini 2.5 Flash on the free tier (giving us an effective 14,400 Requests Per Day). Robust regex parsing guarantees clean JSON output despite the conversational nature of Gemma.
- **Image Generation Engine (`image_generator.py`):** The agent generates a single universal `news_image_universal.png` asset per run using `pollinations.ai`. It uses `Pillow` to programmatically overlay Dark Theme styling (`#143d59` gradient, `#F4B41A` yellow highlight boxes, `#cdcdff` text). It also utilizes `FontAwesome` to automatically generate white vector icons for the Facebook and LinkedIn watermarks.
- **Make.com Scenario (Integration Webhooks):** A fully configured Make.com scenario with a Custom Webhook → Router → 3 platform routes (Facebook, LinkedIn, Instagram). The Router uses `platform` field filters to direct each webhook hit to the correct module.
- **Publishers (all via `make_webhook.py`):**
  - `Facebook` — ✅ Live. Sends `multipart/form-data` with binary image. Make.com → Facebook Pages "Create a Post with Photos".
  - `LinkedIn` — ✅ Live. Sends `multipart/form-data` with binary image. Make.com → LinkedIn "Create a Company Image Post". Maps `image.name` → `fileName` and `image.data` → `data`.
  - `Instagram` — ✅ Pipeline built, Make.com mapping in progress. Sends clean JSON with `image_url` (a public JPEG URL). Make.com → Instagram for Business "Create a photo post". Maps `image_url` → `Photo URL`.
- **CLI Orchestration:** `main.py` is fully configurable via `argparse`, allowing testing of individual platforms (`--platform facebook|linkedin|instagram|all`) and enforcing live/draft mode execution (`--draft true|false`).

## Instagram Integration — Technical Notes
*(Full details in `.docs/instagram_integration.md`)*

The Instagram pipeline required three specific engineering decisions:

1. **PNG → JPEG Conversion:** Instagram Graph API strictly requires JPEG. The engine converts `news_image_universal.png` to JPEG **in-memory** using Pillow before any upload. No temp file is written to disk.

2. **Public Image URL via Catbox/Dropbox:** Instagram refuses binary uploads — it needs a public HTTPS URL. `make_webhook.py` uploads the JPEG to an image host and injects the returned URL as `image_url` in the webhook payload. The host is configurable via `.env`:
   - `IMAGE_HOST=catbox` → Catbox.moe (free, anonymous, for testing)
   - `IMAGE_HOST=dropbox` → Dropbox API (reliable, permanent, for production; requires `DROPBOX_ACCESS_TOKEN`)

3. **JSON payload for Instagram only:** Unlike Facebook/LinkedIn (which send `multipart/form-data` with binary), Instagram sends a **clean JSON payload**. This is critical — multipart buries form fields from Make.com's webhook mapper, making `image_url` invisible. Instagram is explicitly excluded from the `files` block in `make_webhook.py`.

## Make.com Schema — Critical Warning
The Make.com webhook stores ONE data structure schema at a time. **Never re-determine schema using the Instagram JSON payload in isolation** — it wipes the binary `image.name`/`image.data` fields that LinkedIn and Facebook modules depend on.

**Always retrain using multipart mode:**
```bash
# 1. Click Webhook module → "Re-determine data structure" in Make.com
# 2. Run:
python tests/test_instagram_webhook.py --retrain
```
This sends a multipart payload that contains ALL fields: `platform`, `text`, `image_url`, `image.name`, `image.data`, `image.mime`.

The `--instagram` flag (JSON only) is available for isolated testing but must always be followed by `--retrain`.

## Pending Blockers
- **Instagram Live Test:** The full end-to-end Instagram post (Python → Catbox → Make.com → Instagram Graph API) has not yet been confirmed live. Next step: run `--retrain` to restore the Make.com schema, then test with `python main.py --platform instagram`.
- **Dropbox Setup (Optional):** For production reliability, generate a Dropbox API token and set `IMAGE_HOST=dropbox` + `DROPBOX_ACCESS_TOKEN=<token>` in `.env`. Until then, Catbox is the active host.

## Next Steps / Future Roadmap
- [ ] **Confirm Instagram Live Post:** Run full end-to-end test after Make.com schema is restored.
- [ ] **Switch to Dropbox:** For production robustness, configure Dropbox as the image host.
- [ ] **Expanded Sourcing:** Add substantially more RSS feeds (TechCrunch, specialized Substacks) to provide a deeper pool of news for the LLM to curate.
- [ ] **The Telegram Bot:** Build a Webhook/Telegram integration so co-founders can trigger the agent on-demand, specifying exactly how many posts to generate.
- [ ] **The Video Engine (Shorts/Reels):** Implement an `ffmpeg`-based pipeline to convert our visual assets and LLM scripts into automated vertical videos with AI voiceovers, unlocking YouTube, TikTok, and Instagram Reels.
- [ ] **Build `x_twitter.py`:** Add X (Twitter) to the publisher stack to capture the highly active AI tech community.
- [ ] **The Web Hub:** Revive `genai-pro.com` with an integrated Beehiiv/ConvertKit newsletter capture form.
- [ ] **Monetization:** Update LLM prompts to seamlessly inject newsletter CTAs and affiliate links into the social copy.

## Session Memory
*This file serves as a persistent memory bank. If context is lost or a new chat session is opened, the user can instruct the AI to read `.docs/project_context.md` to instantly get up to speed.*
