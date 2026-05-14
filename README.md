# GenAI Pro - Social Media Agent

An autonomous Python agent designed to curate Generative AI news, draft platform-specific social media posts, generate branded visual assets, and publish them natively to social networks.

## Features
- **Automated News Curation**: Fetches RSS feeds from leading AI research labs and uses Google's `Gemma 3` model to curate the top stories.
- **State Manager (Duplicate Protection)**: Persistently tracks discovered articles in `data/articles_state.json` to guarantee the agent only publishes genuinely new articles, safely halting if no fresh news is found.
- **Resilient AI Pipeline**: Features an Exponential Backoff Retry mechanism to natively bypass Google API `504` timeouts, keeping the agent crash-proof.
- **Dynamic Image Generation**: Synthesizes a vibrant, 3D cartoonized background image. Overlays a highly professional `Roboto-Black` headline with high-contrast inverted highlight boxes. Automatically stamps a 220px circular 5-Star agency badge watermark in the top corner using Pillow.
- **Make.com Webhook Bridge**: Bypasses strict LinkedIn/Facebook API limitations by routing a unified `multipart/form-data` payload containing the text and image directly into a Make.com Custom Webhook for flawless enterprise-grade distribution.
- **GitHub Actions CI/CD**: Fully automated deployment running on a 6-hour cron schedule. It executes the entire pipeline securely in the cloud and automatically commits state tracking back to the repository for true zero-touch autonomy.

## Setup & Installation

**1. Install Dependencies**
We recommend using Miniconda or a virtual environment:
```bash
python -m pip install -r requirements.txt
```

**2. Environment Variables**
Copy `.env.template` to `.env` and fill in your API keys:
```env
# Core Settings
AUTONOMOUS_MODE=False

# API Keys
GEMINI_API_KEY="your_google_ai_studio_key"

# Publisher Webhook
MAKE_WEBHOOK_URL="your_make_com_webhook_url"
```

## Usage

You can run the agent locally via the command line. By default, it will draft posts for all platforms and save them (along with the generated image) to the `drafts/` folder.

```bash
python main.py
```

### Command Line Arguments
Use the built-in CLI flags for targeted testing and execution:

- `--platform`: Target a specific platform or run all. Options: `facebook`, `linkedin`, `all` (default: `all`).
- `--draft`: Override the `.env` settings to force a draft (saving locally) or a live autonomous post. Options: `true`, `false`.

**Examples:**
```bash
# Generate drafts for Facebook only
python main.py --platform facebook --draft true

# Force a LIVE autonomous post to all configured platforms
python main.py --draft false
```

## Architecture
- `src/core/fetcher.py`: RSS feed ingestion.
- `src/core/state_manager.py`: Local database ensuring no duplicate posts are generated.
- `src/core/llm_processor.py`: Gemini prompt engineering, markdown sanitization, and exponential backoff retry loops.
- `src/core/image_generator.py`: Visual asset synthesis using Pillow (`courbd.ttf` and `fa-brands-400.ttf`).
- `src/publishers/make_webhook.py`: Unified `multipart/form-data` bridge pushing images and text to Make.com.

## Future Roadmap
- **Database Archiving**: Build a Google Sheets integration to automatically offload articles from `data/state.json` that are older than 30 days. This will prevent the JSON file from bloating to thousands of records while preserving the historical publication data for analytics.
- **Video Generation**: Re-integrate the FFmpeg and Edge-TTS video generation pipeline to expand publishing to TikTok and YouTube Shorts.
