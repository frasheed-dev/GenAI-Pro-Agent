# MoneyPrinterTurbo - Technical Reference & Architectural Analysis

*Location:* `DEVELOPMENT/MoneyPrinterTurbo-main`  
*Purpose:* Technical reference library for GenAI Pro's Q3 Short-Form Video (Reels/Shorts) Engine.

---

## 💡 Overview

MoneyPrinterTurbo is an open-source, all-in-one AI short video generator. Its key technical feature is that **it generates vertical 9:16 MP4 videos on a standard CPU without requiring local GPU hardware.**

Instead of performing heavy local AI video diffusion (which requires high VRAM GPUs), MoneyPrinterTurbo uses a **zero-cost CPU composition pipeline**:
1. **Script & Keywords:** Cloud LLM (Gemini / OpenAI / Kimi).
2. **Footage Retrieval:** Pexels, Pixabay, & Coverr stock video APIs.
3. **Voice Synthesis:** Edge TTS (Microsoft Edge's free cloud speech API) with subtitle timing metadata.
4. **Video Assembly:** FFmpeg & MoviePy CPU stitching.

---

## 🛠️ Key Modules & Extractable Code Patterns

The following Python modules in `MoneyPrinterTurbo-main/app/services` contain clean implementation patterns that we can reference when building GenAI Pro's `video_generator.py`:

### 1. `app/services/voice.py` — Zero-Cost Edge TTS Engine
* **Technology:** Uses `edge-tts` (Microsoft's free cloud TTS service).
* **Why it matters for GenAI Pro:** Requires zero API keys and zero GPU. Produces ultra-crisp, natural voices (`en-US-ChristopherNeural`, `en-US-AvaNeural`) and returns exact word-by-word timestamps required for syncing subtitles.
* **Extraction Plan:** Adapt their async `edge-tts` wrapper directly into `src/core/tts_engine.py`.

### 2. `app/services/video.py` — CPU Video Composition
* **Technology:** Uses `MoviePy` and `FFmpeg` command-line execution.
* **Why it matters for GenAI Pro:** Demonstrates how to take visual background assets (images or MP4 clips), background music, and TTS voiceovers and combine them into a 1080x1920 (9:16) video rendered on a free GitHub Actions CPU runner.
* **Extraction Plan:** Reference their clip resizing, audio mixing, and FFmpeg parameter tuning in `src/core/video_generator.py`.

### 3. `app/services/subtitle.py` — Kinetic Captions & Subtitles
* **Technology:** Generates ASS (Advanced SubStation Alpha) and SRT subtitle files with custom font styling, outline strokes, and highlight colors.
* **Why it matters for GenAI Pro:** Short-form video platforms (Reels/TikTok/Shorts) require high-contrast, word-by-word animated captions for mobile viewers watching on mute.
* **Extraction Plan:** Adapt their ASS file generator into `src/core/kinetic_captions.py`.

### 4. `app/services/material.py` — Stock B-Roll Footage
* **Technology:** Connects to Pexels, Pixabay, and Coverr REST APIs to fetch 9:16 video clips based on search terms.
* **Why it matters for GenAI Pro:** Optional enhancement if we want to mix real stock B-roll clips behind our news text overlays alongside our Google Nano Banana background cards.

---

## ⚖️ Architectural Comparison: MoneyPrinterTurbo vs. GenAI Pro

| Feature | MoneyPrinterTurbo | GenAI Pro |
|---|---|---|
| **Primary Goal** | Faceless generic video creator (user-driven GUI) | Autonomous AI Tech News Publishing Agency |
| **Execution Model** | Standalone FastAPI + Streamlit WebUI | Autonomous Headless Cron Pipeline (CI/CD) |
| **Visual Style** | Generic Pexels stock video clips | Custom branded AI news cards (Google Nano Banana + Pillow text highlights & branding) |
| **Publishing** | Interactive web UI trigger | Make.com webhook -> LinkedIn, Facebook, Instagram |

---

## 📌 Recommendation for GenAI Pro

We will **not** run MoneyPrinterTurbo as a standalone WebUI server because GenAI Pro requires an autonomous, headless pipeline tailored for high-signal AI news. 

Instead, we maintain `MoneyPrinterTurbo-main` as an **in-workspace reference library**. When implementing our Q3 Video Engine (`src/core/video_generator.py`), we will extract its `edge-tts` voice synthesis and FFmpeg composition patterns.
