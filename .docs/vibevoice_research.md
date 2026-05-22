# VibeVoice — Research Findings & Integration Verdict
*Reviewed by: Antigravity — 2026-05-23*
*Repo location: `VibeVoice-main/` (local copy of https://github.com/microsoft/VibeVoice)*

---

## What VibeVoice Is

VibeVoice is a **family of three Microsoft open-source frontier voice AI models**:

| Model | Size | Purpose | Status |
|---|---|---|---|
| **VibeVoice-TTS-1.5B** | 1.5B params | Long-form multi-speaker TTS (up to 90 min, 4 speakers, podcast-quality) | ❌ **Disabled** — code pulled due to deepfake misuse (Sept 2025) |
| **VibeVoice-Realtime-0.5B** | 0.5B params | Real-time streaming TTS, single speaker, ~200ms first-chunk latency | ✅ **Available** — model weights on HuggingFace, inference script present |
| **VibeVoice-ASR-7B** | 7B params | Long-form speech recognition (60-min, diarization, timestamps) | ✅ **Available** — not relevant to our use case |

---

## The Model We Can Actually Use: VibeVoice-Realtime-0.5B

### What it offers
- **Voice quality:** Significantly better than Edge TTS (rule-based). Uses a diffusion-based acoustic head on top of Qwen2.5 0.5B LLM — produces natural, expressive speech with conversational prosody.
- **Available English voices (pre-built .pt presets, already in the repo):**
  - `Carter` (man), `Davis` (man), `Frank` (man), `Mike` (man)
  - `Emma` (woman), `Grace` (woman)
- **Inference:** Takes a `.txt` file + speaker name → outputs `.wav` file. Simple Python call.
- **Latency:** ~200ms first chunk. For our offline batch video generation use case, total generation time is the only metric that matters (not streaming latency).
- **Word-level timestamps:** ❌ **Not natively available.** The model outputs a WAV file only. There is no built-in word-boundary event (unlike Edge TTS which emits `WordBoundary` events used by `tts_engine.py`).

### What it does NOT offer (vs Edge TTS)
- **No word-level timestamps out of the box** → kinetic karaoke captions cannot sync to VibeVoice audio without a secondary ASR pass.
- **Requires GPU for real-time performance.** On CPU, generation is slower than real-time. GitHub Actions runners are CPU-only — this makes VibeVoice unsuitable for cloud-automated runs.
- **Requires model download on first run** (~500MB from HuggingFace). GitHub Actions would need to cache this or download each run.
- **Research license only** — Microsoft explicitly states "not recommended for commercial or real-world applications without further testing." For a B2B SaaS product, this is a risk to document.

---

## Integration Assessment for GenAI Pro

### The Core Problem: Timestamps for Kinetic Captions
Our Reels pipeline requires word-level timestamps to drive kinetic karaoke captions. VibeVoice-Realtime does NOT produce these. 

Two solutions exist:
1. **Run VibeVoice ASR on the generated audio** (ironic — use their ASR model on the TTS output to recover timestamps). This adds a second 7B model call, significant RAM/VRAM overhead, and latency.
2. **Use a third-party forced alignment tool** (e.g., `whisperx`, `montreal-forced-aligner`) to align the known text to the generated audio and extract word timestamps. Adds a dependency but is robust.

### CPU Benchmark — Live Test Results (2026-05-23)

Test script: ~50 tokens / ~12.67 seconds of audio / `Carter` voice / Windows CPU (no GPU)

```
Generation time: 73.71 seconds
Audio duration:  12.67 seconds
RTF:             5.82x
```

**Projected generation times for Reels narration:**

| Narration length | Estimated CPU time |
|---|---|
| 20s (short punchy Reel) | ~2 minutes |
| 35s (5-slide standard Reel) | ~3.5 minutes |
| 60s (long-form) | ~6 minutes |

**Audio quality verdict:** Natural, human-sounding voice. Confirmed acceptable for production Reels content.

### Deployment Feasibility

| Scenario | Verdict |
|---|---|
| **Local machine (CPU, Windows)** | ✅ Viable. 3-4 minutes per Reel is acceptable for a manual trigger workflow. |
| **Local machine (GPU)** | ✅ Excellent. RTF would drop to ~0.3-0.5x — near-instant generation. |
| **GitHub Actions (cloud CI/CD, current setup)** | ⚠️ Not recommended for automation. Cloud CPUs slower than local — RTF likely 10-15x. Reserve for future if GitHub Actions compute budget allows. |
| **Dedicated GPU cloud (Modal.com, RunPod)** | ✅ Viable long-term. Not needed at current scale. |

---

## Verdict: Use VibeVoice for LOCAL Generation; Keep Edge TTS for Cloud

### Recommended hybrid approach:
- **Local video generation workflow** (triggered manually or via Telegram bot):
  - Use **VibeVoice-Realtime-0.5B** (`Carter` or `Davis` voice) for high-quality audio
  - Run **whisperx** forced alignment on the WAV output to recover word timestamps
  - Feed timestamps into existing `kinetic_captions.py` (no changes needed to the captions engine)
  - Output: premium-quality Reel with natural voice + kinetic captions
  
- **Automated cloud workflow (GitHub Actions)**:
  - Keep **Edge TTS** for fully autonomous runs (zero GPU requirement, native word boundary events)
  - Accept slightly lower voice quality in exchange for zero-cost, always-on automation

### Best voice for GenAI Pro brand:
- **`Carter`** (male, natural American English) — closest to a credible analyst/newsreader voice
- **`Davis`** (male, slightly more casual) — second choice

---

## Setup Steps (Local)

```bash
# 1. Install VibeVoice streaming TTS extras (from VibeVoice-main/)
pip install -e .[streamingtts]

# 2. Install forced alignment for word timestamps
pip install whisperx

# 3. Generate audio (model downloads automatically from HuggingFace on first run)
python VibeVoice-main/demo/realtime_model_inference_from_file.py \
  --model_path microsoft/VibeVoice-Realtime-0.5B \
  --txt_path drafts/script.txt \
  --speaker_name Carter \
  --output_dir drafts/

# 4. Run forced alignment to get word timestamps
# (integrate into src/core/tts_engine.py via a vibevoice_tts() function)
```

---

## Files to Create for Integration
| File | Purpose |
|---|---|
| `src/core/tts_vibevoice.py` | New TTS adapter wrapping VibeVoice inference + whisperx forced alignment → outputs WAV + word timestamp JSON (same format as `tts_engine.py`) |
| Update `src/core/video_generator.py` | Add `--tts-engine vibevoice|edge` flag to `generate_audio()` to switch between engines |

---

## Key Risk
Microsoft's license explicitly states this model is for **research and development purposes only** and is "not recommended for commercial applications." For GenAI Pro's SaaS productization path, the audio should be disclosed as AI-generated (`#AIGenerated`). This is already planned for automated posts.
