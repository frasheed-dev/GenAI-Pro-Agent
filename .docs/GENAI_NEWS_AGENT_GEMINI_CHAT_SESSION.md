# Gen AI Pro: Complete Chat Session Summary & Project Handover
**Date:** May 2026
**Project:** Gen AI Pro Autonomous News Agency

This document serves as a complete brain-dump and context handover from our previous chat session. If you are starting a new chat session with an AI agent, instruct them to read this file to instantly regain full context of the project.

---

## 1. Project Overview
We have successfully built a fully autonomous, zero-touch news agency pipeline. The system runs on GitHub Actions, fetches RSS feeds, uses Gemini to curate and draft social media posts, dynamically generates premium branded graphics via Pillow, and publishes autonomously to Facebook, LinkedIn, and Instagram via Make.com.

## 2. Technical Architecture & Components

### A. The Curation & Drafting Engine (`src/core/llm_processor.py`)
- **RSS Feeds:** We use Feedly/RSS endpoints to grab the latest AI news.
- **Gemini Selection:** Gemini curates the top stories that match our "GenAI, autonomous agents, and massive tech moves" standard.
- **Social Drafting:** The LLM drafts platform-specific posts using a strict 3-part layout:
  1. The TL;DR (Hook + Bullets)
  2. Why it Matters (Opinionated Influencer Take)
  3. The Hook-and-Hold CTA (Question to drive comments)
- **Instagram Fix:** The prompt explicitly avoids raw URLs for Instagram and tells Gemini to use "Link in Bio" instead.
- **Formatting Fix:** Gemini is strictly instructed *not* to output literal meta-headers (like "1. THE TL;DR") so the posts look organic.

### B. The Image Rendering Engine (`src/core/image_generator.py`)
- **Backgrounds:** Generates 1080x1350 images (Instagram-optimized aspect ratio).
- **Dynamic Highlighting:** Words marked with asterisks (`*word*`) are highlighted with a signature yellow box (`#F4B41A`). 
  - **The "Status Quo" Fix:** We implemented logic to pre-scan lines and calculate the `max_hl_descent`. This ensures contiguous highlighted words have a perfectly flush, unified bounding box instead of looking jagged.
- **Typography:** We use pure local fonts to avoid broken download links.
  - Headline/Text: `Roboto-Black.ttf`
  - Social Links/Footer: `Roboto-Black.ttf`
  - Icons: `fa-brands-400.ttf`
- **Social Footer:** Centered `ig_x` layout featuring Facebook (`/genaipro`), Instagram (`@gen_ai_pro`), and LinkedIn (`/company/genaipro`).

### C. The Typographic Brand Logo
- We discarded external PNG graphics for a purely programmatic "App Icon" logo.
- A perfect circle with a semi-transparent dark background (`fill=(0, 0, 0, 180)`).
- **Text:** Stacked "Gen AI" (White & Yellow) and "Pro" (Yellow) dynamically centered inside the badge.

### D. The Make.com Webhook Integration (`src/publishers/make_webhook.py`)
- The script passes a `platform` and `text` payload to a Make.com Custom Webhook.
- Make.com uses a Router to split the logic between Facebook, LinkedIn, and Instagram for Business.
- **The Instagram API Bypass:** Because Instagram's API requires a public image URL (and rejects direct file uploads), our Python script seamlessly uploads the binary image to `Catbox.moe` whenever `platform == "instagram"`. It captures the public URL and passes it to Make.com via the `image_url` variable.
- **Webhook Schema Fix:** `image_url` is initialized as `""` for all platforms so that Make.com's "Determine data structure" listener always learns the schema correctly.

### E. Social Profile Logo Generator (`tests/generate_social_logo.py`)
- Since social profiles require solid backgrounds, we created a script that geometrically scales up the watermark logo by 5x onto a massive 1000x1000 dark navy (`#143d59`) canvas.

---

## 3. GitHub Actions CI/CD
- The repository is fully automated via GitHub Actions (`run_agent.yml`).
- It triggers on a cron schedule or via manual workflow dispatch.
- **Resilience:** The script uses `requests` timeouts to prevent endless hanging if Make.com or an RSS feed goes down, ensuring we don't consume all GitHub Action minutes.

---

## 4. Next Steps for Business Scaling
Now that the technical infrastructure is 100% complete and autonomous, the next goals are:
1. **Audience Acquisition:** Utilizing the new Instagram integration to capture highly visual traffic.
2. **Engagement Tools:** Potentially building a comment auto-responder in Make.com.
3. **Newsletter Expansion:** Converting the daily news summaries into a weekly Substack/Beehiiv email.
4. **Video Content:** Reactivating the `GENERATE_VIDEO` flag to create short-form content for TikTok/Reels.
