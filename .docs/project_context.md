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
- **Image Generation Engine (`image_generator.py`):** The agent generates a single universal `news_image_universal.png` asset per run. **We have migrated the execution environment to a dedicated Raspberry Pi 4 on a residential IP.** Originally, we attempted to use `pollinations.ai` to generate SDXL images. However, `pollinations.ai` has since started aggressively rate-limiting residential IPs with `402 Queue Full` errors. To completely eliminate the need to rely on third-party APIs, **we are migrating to OnnxStream to run SDXL Turbo entirely locally on the Raspberry Pi.** Once verified, the full agent setup will reside in `/home/frasheed-dev/development/genai-pro`. The script still uses `Pillow` to programmatically overlay Dark Theme styling (`#143d59` gradient, `#F4B41A` yellow highlight boxes, `#cdcdff` text) and `FontAwesome` for vector social icons.
- **Make.com Scenario (Integration Webhooks):** A fully configured Make.com scenario with a Custom Webhook → Router → 3 platform routes (Facebook, LinkedIn, Instagram). The Router uses `platform` field filters to direct each webhook hit to the correct module.
- **Publishers (all via `make_webhook.py`):**
  - `Facebook` — ✅ Live. Sends `multipart/form-data` with binary image. Make.com → Facebook Pages "Create a Post with Photos".
  - `LinkedIn` — ✅ Live. Sends `multipart/form-data` with binary image. Make.com → LinkedIn "Create a Company Image Post". Maps `image.name` → `fileName` and `image.data` → `data`.
  - `Instagram` — ✅ **Live and confirmed end-to-end (2026-05-22).** Sends clean JSON with `image_url` (a public JPEG URL via ImgBB). Make.com → Instagram for Business "Create a photo post". Maps `image_url` → `Photo URL`.
- **CLI Orchestration:** `main.py` is fully configurable via `argparse`, allowing testing of individual platforms (`--platform facebook|linkedin|instagram|all`) and enforcing live/draft mode execution (`--draft true|false`).

## Reference Assets & Documentation
- **MoneyPrinterTurbo (`.docs/moneyprinterturbo_reference.md`):** Located at `DEVELOPMENT/MoneyPrinterTurbo-main`. Referenced as a code library for zero-GPU CPU video composition (FFmpeg/MoviePy), zero-cost Microsoft `edge-tts` voice synthesis, and ASS subtitle generation for GenAI Pro's Q3 Short-Form Video Engine.

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

## Platform Performance Data (as of 2026-05-22)

| Platform | Status | 7-Day Results | Key Insight |
|---|---|---|---|
| **LinkedIn** | ✅ Best channel | ~1,999 impressions / 15 days, 30 reactions | Personal profile (Farhan, PhD) outperforms company page. Data-backed analytical posts 30-40× better than opinion posts. |
| **Facebook** | ✅ Live, low ROI | 321 views / 7 days, 2 net follows | Structurally throttled for new pages — Facebook's business model. Keep posting (zero cost), no extra engineering investment until 1K+ followers. |
| **Instagram** | ✅ Live, zero reach (static) | 0 views, 0 interactions | Instagram's algorithm does not distribute static image posts from new accounts. Static image posts are effectively invisible. Reels is the only organic growth lever. |

## Pending Blockers
- **Instagram Static Images = Zero Reach:** Confirmed after 7 days of live data. Static image posts on Instagram receive 0 organic views from non-followers. The pipeline is technically working but the format is the bottleneck. **Fix: Build the Reels/Short-Form Video pipeline.** This is the #1 next technical priority.
- **Dropbox Setup (Optional):** For production reliability, generate a Dropbox API token and set `IMAGE_HOST=dropbox` + `DROPBOX_ACCESS_TOKEN=<token>` in `.env`. ImgBB is the current active host and working reliably from GitHub Actions cloud IPs.

- [x] **Journalistic 3-Slide Carousel Deck Engine (2026-07-27):** Built a 3-slide visual carousel card deck generator (`carousel_slide_1.png`, `slide_2.png`, `slide_3.png`) in 1080x1350 vertical resolution. Enforces a strict journalistic, objective, non-hype tone. Uses AI background when available, or our programmatic dark navy-teal gradient background as a zero-cost guaranteed fallback.
- [ ] **Path A: Telegram Engagement Alert Assistant (PLANNED):** Monitor posts from top 100 AI voices and companies. When a major post drops, Gemma 3 drafts a 1-line analyst-grade comment (strictly non-slop, dry, data-backed) and sends a Telegram alert with a 1-click link to Farhan for safe, ban-free manual posting.
- [ ] **Beehiiv Newsletter — HIGH PRIORITY:** Start now even with 0 subscribers. Email is the only owned audience asset; social algorithms are unreliable. Simple landing page + newsletter subscribe form.
- [ ] **Expanded Sourcing:** Add substantially more RSS feeds (TechCrunch, specialized Substacks) to provide a deeper pool of news for the LLM to curate.
- [ ] **Switch to Dropbox:** For production robustness, configure Dropbox as the image host (ImgBB working for now).
- [ ] **Build `x_twitter.py`:** X (Twitter) integration paused (API cost $100/month). Code preserved. Reactivate when other platforms show meaningful traction.
- [ ] **The Web Hub:** Revive `genai-pro.com` with an integrated Beehiiv newsletter capture form.
- [ ] **SaaS Abstraction:** Refactor the agent for multi-niche deployment (crypto, finance, real estate) at $99-299/month. Core architecture is already niche-agnostic.
- [ ] **Monetization:** Update LLM prompts to inject newsletter CTAs and affiliate links into social copy.

## Session Memory
*This file serves as a persistent memory bank. If context is lost or a new chat session is opened, the user can instruct the AI to read `.docs/project_context.md` to instantly get up to speed.*
