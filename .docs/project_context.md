# GENAI_PRO - Project Context (Updated May 2026)

## Project Goal
GenAI Pro has evolved from a technical scripting project into an active **Media-to-SaaS Business Venture**. 

Our strategic funnel is:
1. **Automated Media:** Use our "Zero-Cost Content Engine" to autonomously publish high-signal Generative AI news to social media platforms (Facebook, LinkedIn, X) to farm organic impressions.
2. **Audience Capture:** Funnel social traffic to our owned web property (`genai-pro.com`) to build a highly lucrative B2B newsletter.
3. **Monetization:** Generate revenue through high-ticket newsletter sponsorships, affiliate marketing, and eventually productizing the Agent architecture itself as a B2B SaaS offering.

*(For detailed timelines, see `.docs/business_plan_2026.md`)*

## Current State (What is completed)
- **Core Architecture Built:** A modular system located in `src/core` that fetches RSS feeds (OpenAI, Anthropic, Google) and curates them.
- **The Gemma 3 LLM Brain:** We utilize the Developer API to access `gemma-3-27b-it`, Google's highly capable open-weights model. We explicitly shifted to this model to bypass the strict daily rate limits placed on Gemini 2.5 Flash on the free tier (giving us an effective 14,400 Requests Per Day). Robust regex parsing guarantees clean JSON output despite the conversational nature of Gemma.
- **Image Generation Engine (`image_generator.py`):** The agent generates a single universal `news_image_universal.png` asset per run using `pollinations.ai`. It uses `Pillow` to programmatically overlay Dark Theme styling (`#143d59` gradient, `#F4B41A` yellow highlight boxes, `#cdcdff` text). It also utilizes `FontAwesome` to automatically generate white vector icons for the Facebook and LinkedIn watermarks.
- **Publishers:** 
  - `facebook.py` is fully operational and capable of uploading photos alongside text to the GenAI Pro Facebook Page.
  - `linkedin.py` is written and ready, awaiting API access.
- **CLI Orchestration:** `main.py` is fully configurable via `argparse`, allowing testing of individual platforms (`--platform facebook|linkedin|all`) and enforcing live/draft mode execution (`--draft true|false`).

## Pending Blockers
- **LinkedIn Agent Live Test:** The code for `src/publishers/linkedin.py` is fully written, but the live test to post directly to the GenAI Pro Company Page is **currently blocked**. We are waiting for LinkedIn to approve the "Community Management API" request. Once approved, the user must generate the OAuth token with `w_organization_social`, add it to `.env`, and implement the 3-step UGC image upload flow for LinkedIn.

## Next Steps / Future Roadmap
- [ ] **Expanded Sourcing:** Add substantially more RSS feeds (TechCrunch, specialized Substacks) to provide a deeper pool of news for the LLM to curate.
- [ ] **The Telegram Bot:** Build a Webhook/Telegram integration so co-founders can trigger the agent on-demand, specifying exactly how many posts to generate.
- [ ] **The Video Engine (Shorts/Reels):** Implement an `ffmpeg`-based pipeline to convert our visual assets and LLM scripts into automated vertical videos with AI voiceovers, unlocking YouTube, TikTok, and Instagram.
- [ ] **Infrastructure Phase:** Upgrade `linkedin.py` for image support, build `x_twitter.py`, and automate everything via GitHub Actions.
- [ ] **The Web Hub:** Revive `genai-pro.com` with an integrated Beehiiv/ConvertKit newsletter capture form.
- [ ] **Monetization:** Update LLM prompts to seamlessly inject newsletter CTAs and affiliate links into the social copy.

## Session Memory
*This file serves as a persistent memory bank. If context is lost or a new chat session is opened, the user can instruct the AI to read `.docs/project_context.md` to instantly get up to speed.*
