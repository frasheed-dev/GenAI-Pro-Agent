# GenAI Pro - Raspberry Pi 4 Migration Guide

This guide covers setting up the GenAI Pro agent on a dedicated Raspberry Pi 4 to act as our autonomous, free, 24/7 server.

## Why Migrate to a Raspberry Pi?
1. **Bypass Cloud API Limits:** Third-party APIs (Hugging Face, Together.ai) enforce strict paywalls. The free `pollinations.ai` API works flawlessly, but they block shared cloud IP addresses (like GitHub Actions) with `402 Queue Full` errors to prevent spam. By running the agent from your home Wi-Fi via the Pi, you get **unlimited, free SDXL image generation forever**.
2. **Video Rendering:** We will soon deploy heavy `ffmpeg` video rendering for Instagram Reels. GitHub Actions will time out on these heavy processing tasks. The Pi 4 (4GB) has enough processing power to slowly render these videos locally at $0 cost.
3. **Data Security:** API Keys (`GEMINI_API_KEY`, etc.) remain safely on your physical machine rather than floating in GitHub Secrets.

## Prerequisites
- A Raspberry Pi 4 (4GB or 8GB recommended).
- Raspberry Pi OS (Debian/Ubuntu) installed and connected to the internet.
- SSH access to your Pi from your main computer.

---

## Step 1: System Dependencies
First, SSH into your Raspberry Pi and install the required core packages: Git, Python 3, and FFmpeg (for video generation).

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3-pip python3-venv ffmpeg libsm6 libxext6
```

## Step 2: Clone Repository & Virtual Environment
Clone the GenAI Pro repository onto your Pi and set up a secure, isolated Python environment.

```bash
# Clone the repository
git clone https://github.com/[YOUR-GITHUB-USERNAME]/genai-pro.git
cd genai-pro

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the required Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Secure Environment Variables
Create the `.env` file on the Pi to securely store your API keys. **Do not commit this file.**

```bash
nano .env
```

Paste the following variables into the file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
MAKE_WEBHOOK_URL=your_make_webhook_url_here
IMGBB_API_KEY=your_imgbb_api_key_here
AUTONOMOUS_MODE=True
IMAGE_HOST=imgbb
```
*(Note: You do NOT need `HF_TOKEN` or `TOGETHER_API_KEY` anymore, as Pollinations.ai will work natively on your home IP).*

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

## Step 4: Automate with Cron (The "Always-On" Agent)
We use `cron` to tell the Pi exactly when to wake up, fetch the news, generate images, and trigger the Make.com webhook.

Open the cron editor:
```bash
crontab -e
```

Add the following schedule to the bottom of the file to run the script automatically 3 times a day (e.g., 9:00 AM, 2:00 PM, and 7:00 PM). Adjust times as needed.

```bash
# m h  dom mon dow   command
0 9,14,19 * * * cd /home/pi/genai-pro && /home/pi/genai-pro/venv/bin/python main.py >> /home/pi/genai-pro/agent.log 2>&1
```

*(Verify that your repository path is `/home/pi/genai-pro`. If your username is different, update the paths accordingly).*

## Step 5: Decommission GitHub Actions
Once the Pi successfully posts its first autonomous update, go to your GitHub repository and **delete** the `.github/workflows/agent_cron.yml` file to prevent duplicate posts and clean up your cloud infrastructure.

---
**Status:** The agent is now successfully deployed on hardware you own, executing at a 100% discount with zero external compute limits.
