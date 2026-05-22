import google.generativeai as genai
from core.config import GEMINI_API_KEY
import json
import time
import re

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Use the recommended model for general text tasks
model = genai.GenerativeModel('gemini-3.1-flash-lite')

def extract_text(response):
    try:
        return response.text
    except ValueError:
        if response.candidates and response.candidates[0].content.parts:
            return "".join([part.text for part in response.candidates[0].content.parts])
        return ""

def generate_with_retry(prompt, max_retries=5, delay=15):
    """Wraps the Gemini API call with exponential backoff retry logic to handle 504 timeouts."""
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[LLM] Gemini API error: {e}. Retrying in {delay} seconds (Attempt {attempt+1}/{max_retries})...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise e

def curate_articles(articles):
    """
    Takes a list of fetched articles and asks the LLM to identify the 2 most
    important Generative AI news items.
    """
    if not articles:
        return []

    prompt = (
        "You are an expert AI news curator. Review the following recent news articles.\n"
        "Select strictly the top 1 or 2 most impactful developments specifically related to "
        "Generative AI, Large Language Models, or major AI product releases.\n\n"
        "Return the result ONLY as a SINGLE valid JSON list containing the integer indices of the selected articles.\n"
        "Do not include any other text. For example: [0, 3]\n\n"
        "Articles:\n"
    )
    
    for i, article in enumerate(articles):
        prompt += f"[{i}] Source: {article['source']} | Title: {article['title']} | Summary: {article['summary']}\n"
        
    print("Asking Gemini to curate the articles...")
    try:
        response = generate_with_retry(prompt)
        text = extract_text(response).strip()
        # Robustly extract JSON array using non-greedy regex to ignore conversational fluff or multiple arrays
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            text = match.group(0)
            
        selected_indices = json.loads(text.strip())
        
        # Filter the original list based on selected indices
        curated = [articles[i] for i in selected_indices if 0 <= i < len(articles)]
        return curated
    except Exception as e:
        print(f"Error during curation: {e}")
        return []

def draft_social_post(platform, curated_articles):
    """
    Drafts a social media post based on the curated articles, tailored for the given platform.
    """
    if not curated_articles:
        return "No significant GenAI news to post today."

    # ── Platform-specific voice ───────────────────────────────────────────────
    if platform.lower() == "linkedin":
        platform_instructions = (
            "PLATFORM: LinkedIn\n"
            "- Voice: Write like a senior AI researcher sharing insights with industry peers over coffee. "
            "Knowledgeable, direct, occasionally dry about AI hype. Never corporate or press-release-y.\n"
            "- Structure: Start with a single punchy sentence that earns the stop-scroll. "
            "Then deliver your analysis and opinion in short bursts — 1 to 2 sentences, then a blank line, "
            "then the next thought. Never chain more than 2 sentences without a blank line between them. "
            "Close with a statement or question that invites real disagreement — skip it if it feels forced.\n"
            "- Length: 900-1,400 characters.\n"
            "- Format: Short lines. Blank lines between every thought. No bullet points. No walls of text.\n"
        )
    elif platform.lower() == "x" or platform.lower() == "twitter":
        platform_instructions = (
            "PLATFORM: X (Twitter) — single standalone tweet, NOT a thread.\n"
            "- The ENTIRE post must be 260 characters or fewer.\n"
            "- Line 1: One scroll-stopping sentence with a specific fact or counterintuitive angle. Not hype.\n"
            "- Lines 2-3: 2 ultra-short bullets with ⚡ or 🔥 emojis. Max 55 chars each.\n"
            "- Final line: 1-2 hyper-niche hashtags only (e.g. #GenAI #LLMOps). Never #AI or #Tech.\n"
            "- No URLs. No 'Thread:'. No section headers. Write it like a real person, not a bot.\n"
        )
    elif platform.lower() == "facebook":
        platform_instructions = (
            "PLATFORM: Facebook\n"
            "- Voice: Write like a knowledgeable friend explaining big AI news to a curious but "
            "non-technical audience. Warm, approachable, grounded. Never condescending.\n"
            "- If you use a technical term, briefly explain it in plain English right after — inline, not in a separate block.\n"
            "- Structure: One punchy opener sentence. Then a blank line. Then explain the news simply in "
            "short bursts of 1-2 sentences with a blank line between each. Why should a normal person care? "
            "Answer that in 1-2 sentences. End with a genuine conversational question.\n"
            "- Length: 800-1,200 characters. Every sentence should be readable on mobile in a single glance.\n"
            "- Emojis: 2-4 total, placed where they add meaning — not as decoration.\n"
        )
    elif platform.lower() == "instagram":
        platform_instructions = (
            "PLATFORM: Instagram\n"
            "- Voice: Sharp, punchy. Every single line must be able to stand completely alone.\n"
            "- Structure: One hook line (max 8 words). Then a blank line. Then 4-6 standalone lines, "
            "each separated by a blank line. Close with one line that makes someone want to save or share.\n"
            "- CRITICAL: Do NOT include any raw URLs in the caption. Never. Not even shortened ones. "
            "Only write 'link in bio' if there is genuinely something to link to.\n"
            "- Emojis: 1 per line maximum. Purposefully chosen, not decorative.\n"
            "- Length: 500-800 characters. Shorter is better. Read-before-the-fold is the goal.\n"
        )
    else:
        platform_instructions = "- Keep it professional, direct, and genuinely useful to the reader.\n"

    # ── Core prompt ───────────────────────────────────────────────────────────
    prompt = (
        f"You are the voice of GenAI Pro on {platform.capitalize()} — a sharp, slightly irreverent AI "
        "industry analyst who cuts through hype to explain what's actually happening. "
        "Think: technically credible, occasionally dry, always substantive. "
        "You write like a real person who genuinely follows this space, not a content marketing bot. "
        "Your readers are smart, skeptical of AI hype, and can smell a template a mile away.\n\n"

        "Write a post summarizing the following Generative AI news developments.\n\n"

        "STRUCTURAL GUIDANCE (guidelines, not a rigid template to fill in):\n"
        "- Open with a single sentence that earns the stop-scroll: a surprising specific detail, "
        "a counterintuitive angle, or a sharp observation. NOT a rhetorical question. NOT 'Big news:' or 'Hot take:'.\n"
        "- Deliver the actual news with your perspective woven through it. What do you genuinely think? "
        "Your opinion should feel earned, not tacked on.\n"
        "- Close with something that invites a real response: a prediction people can agree or argue with, "
        "or a question with no obvious answer. Avoid 'What do you think?' and 'Thoughts?' endings.\n"
        "- The whole post must read like something a real human wrote in one sitting, not a template filled in.\n\n"

        "BANNED PHRASES — using any of these is an automatic failure:\n"
        "'game-changer', 'revolutionary', 'This changes everything', 'The future is here', "
        "'Let's unpack', 'Let's dive in', 'Mind-blowing', 'Drop your thoughts below', "
        "'The AI race is heating up', 'We're entering a new era', 'Excited to share', "
        "'Hot take:', 'Big news!', 'buckle up', 'It's official', 'paradigm shift', "
        "'The future of AI', 'rapidly evolving', 'landscape'.\n\n"

        "FORMATTING RULES — these are non-negotiable:\n"
        "- Do NOT use markdown like **bold** or *italics* — social platforms show these as literal asterisks.\n"
        "- Do NOT output any section headings or labels from these instructions.\n"
        "- AERATED FORMAT IS MANDATORY: Write in short sentences. Put a blank line after every 1-2 sentences. "
        "No paragraph should ever exceed 2 sentences. Each line must be able to stand alone and pull "
        "the reader to the next. A wall of text is an automatic failure regardless of content quality.\n\n"

        f"{platform_instructions}\n"
    )

    # X has a strict char limit — source links and hashtags are handled in platform_instructions
    is_x = platform.lower() in ("x", "twitter")
    if not is_x:
        prompt += (
            "- Put the Source Links at the very bottom.\n"
            "- Add 3-5 hyper-relevant, niche hashtags at the very end (avoid generic tags like #AI).\n"
        )
    prompt += "\nNews Developments:\n"

    for article in curated_articles:
        prompt += f"- {article['title']} ({article['source']}): {article['summary']} [Link: {article['link']}]\n"

    print(f"Asking Gemini to draft the {platform.capitalize()} post...")
    try:
        response = generate_with_retry(prompt)
        text = extract_text(response).strip()
        # Strip out any residual markdown bold tags since social platforms render them literally
        text = text.replace("**", "")
        return text
    except Exception as e:
        print(f"Error drafting post: {e}")
        return f"Error generation failed. {e}"

def generate_image_metadata(post_content):
    """
    Takes the drafted social post and asks Gemini to generate a headline and background prompt for the image.
    """
    print("Pausing for 15 seconds to respect Gemini Free Tier rate limits...")
    time.sleep(15)
    
    prompt = (
        "Based on the following social media post, generate two things for an image generator:\n"
        "1. 'headline': A punchy 10-15 word headline. Wrap the 1 or 2 most important keywords or phrases in asterisks (e.g. Elon Musk buys *AI Startup* for *$60 Billion*).\n"
        "2. 'image_prompt': A descriptive prompt for an AI image generator to create the background. Do not include text in the prompt. Make it a 3D illustration, cartoonize style, vibrant colors, and relevant to the technology news.\n\n"
        f"Post Content:\n{post_content}\n\n"
        "Return the result strictly as a valid JSON object like this:\n"
        "{\n"
        '  "headline": "...",\n'
        '  "image_prompt": "..."\n'
        "}\n"
    )
    
    print("Asking Gemini to generate image metadata...")
    try:
        response = generate_with_retry(prompt)
        text = extract_text(response).strip()
        
        # Clean up markdown formatting if the LLM wrapped it
        text = text.replace('```json', '').replace('```', '').strip()
        
        try:
            parsed = json.loads(text)
            print(f"[Debug] Parsed Metadata keys: {type(parsed)} {parsed.keys() if isinstance(parsed, dict) else 'Not a dict'}")
            
            # If the LLM returned a list of dicts, grab the first one
            if isinstance(parsed, list) and len(parsed) > 0:
                parsed = parsed[0]
                
            return parsed
        except json.JSONDecodeError:
            # Fallback regex if there's trailing conversational text
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list) and len(parsed) > 0:
                        parsed = parsed[0]
                    return parsed
                except Exception:
                    pass
            print(f"Failed to parse LLM output as JSON:\n{text}")
            return None
    except Exception as e:
        print(f"Error generating image metadata: {e}")
        return None

if __name__ == "__main__":
    sample_articles = [
        {"title": "OpenAI releases GPT-5", "link": "http://openai.com", "source": "OpenAI Blog", "summary": "The new model is here and it is incredibly fast and smart.", "published_at": "2023-10-27"}
    ]
    curated = curate_articles(sample_articles)
    print(f"Curated {len(curated)} articles.")
    post = draft_social_post("linkedin", curated)
    print("\n--- DRAFTED POST ---\n")
    print(post)
    
    metadata = generate_image_metadata(post)
    print("\n--- IMAGE METADATA ---\n")
    print(metadata)
