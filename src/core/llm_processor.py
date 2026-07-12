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

def apply_linkedin_company_tags(text: str) -> str:
    """
    Looks for exact references of major AI and tech companies and replaces them
    with LinkedIn's organization URN tagging format: @[Company Name](urn:li:organization:ID).
    Protects URLs and hashtags by replacing them with temporary placeholders before processing.
    """
    # 1. Extract URLs and replace with placeholders
    url_pattern = r'https?://[^\s]+|www\.[^\s]+'
    urls = re.findall(url_pattern, text)
    for i, url in enumerate(urls):
        text = text.replace(url, f'__URL_PLACEHOLDER_{i}__')
        
    # 2. Extract Hashtags and replace with placeholders
    hashtag_pattern = r'#[a-zA-Z0-9_]+'
    hashtags = re.findall(hashtag_pattern, text)
    for i, hashtag in enumerate(hashtags):
        text = text.replace(hashtag, f'__HASHTAG_PLACEHOLDER_{i}__')

    # 3. Replace company names
    company_map = {
        r'\bOpenAI\b': '@[OpenAI](urn:li:organization:11130470)',
        r'\bAnthropic\b': '@[Anthropic](urn:li:organization:7936402)',
        r'\bNVIDIA\b': '@[NVIDIA](urn:li:organization:3608)',
        r'\bMeta\b': '@[Meta](urn:li:organization:10667)',
        r'\bGoogle\b': '@[Google](urn:li:organization:1441)',
        r'\bMicrosoft\b': '@[Microsoft](urn:li:organization:1035)',
        r'\bCohere\b': '@[Cohere](urn:li:organization:24024765)',
        r'\bMistral\b(\s*AI)?': '@[Mistral AI](urn:li:organization:94273421)',
        r'\bPerplexity\b(\s*AI)?': '@[Perplexity](urn:li:organization:88007673)',
        r'\bMidjourney\b': '@[Midjourney](urn:li:organization:82318617)',
        r'\bxAI\b': '@[xAI](urn:li:organization:5191206)',
        # Fortune 500 Tech & AI giants
        r'\bIBM\b': '@[IBM](urn:li:organization:1009)',
        r'\bIntel\b': '@[Intel](urn:li:organization:1053)',
        r'\bOracle\b': '@[Oracle](urn:li:organization:1028)',
        r'\bCisco\b': '@[Cisco](urn:li:organization:1063)',
        r'\bAdobe\b': '@[Adobe](urn:li:organization:1480)',
        r'\bSalesforce\b': '@[Salesforce](urn:li:organization:3185)',
        r'\bAMD\b': '@[AMD](urn:li:organization:1497)',
        r'\bQualcomm\b': '@[Qualcomm](urn:li:organization:2017)',
        r'\bServiceNow\b': '@[ServiceNow](urn:li:organization:29352)',
        r'\bSnowflake\b': '@[Snowflake](urn:li:organization:3653845)',
        r'\bDatabricks\b': '@[Databricks](urn:li:organization:3477522)',
        r'\bPalantir\b': '@[Palantir Technologies](urn:li:organization:20708)',
        r'\bBroadcom\b': '@[Broadcom](urn:li:organization:3072)',
    }
    
    for pattern, tag in company_map.items():
        text = re.sub(pattern, tag, text, flags=re.IGNORECASE)

    # 4. Restore Hashtags
    for i, hashtag in enumerate(hashtags):
        text = text.replace(f'__HASHTAG_PLACEHOLDER_{i}__', hashtag)

    # 5. Restore URLs
    for i, url in enumerate(urls):
        text = text.replace(f'__URL_PLACEHOLDER_{i}__', url)

    return text

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
            "Next, provide a 'Key Highlights' section with 2-3 short, distinct bullet points (using standard '•' or '-' characters on separate lines) summarizing the core facts. "
            "Then, provide a brief executive summary (1-2 short paragraphs) delivering your analysis and opinion on why it matters. "
            "Close with a statement or question that invites real disagreement.\n"
            "- Length: 500-900 characters. Keep it extremely scannable.\n"
            "- Format: MUST include a bulleted list for the facts. Blank lines between sections. No walls of text.\n"
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
            "- If you use a technical term, briefly explain it in plain English right after.\n"
            "- Structure: One punchy opener sentence. Then a 'Key Highlights' section with 2-3 short, distinct bullet points (using standard '•' or '-' characters on separate lines). "
            "Then explain the news simply in a short executive summary (1-2 paragraphs) answering: Why should a normal person care? "
            "End with a genuine conversational question.\n"
            "- Length: 500-900 characters. Every sentence should be readable on mobile in a single glance.\n"
            "- Emojis: 2-4 total, placed where they add meaning — not as decoration.\n"
            "- Format: MUST include a bulleted list. Blank lines between sections.\n"
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
            "- Put the source links at the very bottom, formatted STRICTLY like this:\n"
            "Sources:\n"
            "[url 1]\n"
            "[url 2]\n"
            "- Add 3-5 hyper-relevant, niche hashtags below the sources (avoid generic tags like #AI).\n"
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
        
        # Append the automated agent disclaimer to all platforms except X (due to char limits)
        if not is_x:
            footer = (
                "\n\n---\n"
                "🤖 Transparency Note: This entire post (curation, image, and text) was generated "
                "and published autonomously by the GenAI Pro Agent.\n\n"
                "We are building the future of automated media. Follow GenAI Pro to watch us build "
                "in public!"
            )
            text += footer
            
        # Apply LinkedIn specific company tags after draft generation is complete
        if platform.lower() == "linkedin":
            text = apply_linkedin_company_tags(text)
            
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
        "Based on the following social media post, generate two things for an image generator:\n\n"
        "1. 'headline': A punchy 10-15 word headline that captures the single most newsworthy fact. "
        "Wrap the 1 or 2 most important keywords or phrases in asterisks (e.g. Elon Musk buys *AI Startup* for *$60 Billion*).\n\n"
        "2. 'image_prompt': A highly detailed prompt for a premium AI image generator. Follow ALL of these rules:\n"
        "   - SUBJECT: Describe ONE clear, specific visual subject that DIRECTLY represents the news story. "
        "     Avoid generic 'technology background' clichés. For example: if the news is about a chatbot, show a "
        "     glowing humanoid AI conversing with a human; if it's about chip manufacturing, show a "
        "     photorealistic silicon wafer being assembled by robotic arms.\n"
        "   - STYLE: Bold, clean digital illustration. Think: a vibrant tech editorial graphic — \n"
        "     flat-ish design with subtle depth, strong silhouettes, and punchy saturated colors \n"
        "     (deep navy, electric teal, amber/gold accents). NOT photorealistic. NOT hyper-detailed. \n"
        "     Simple enough to read at a glance on a phone screen.\n"
        "   - COMPOSITION: The main subject must be in the UPPER or MIDDLE portion of the frame. "
        "     The lower 40% of the image must be darker/simpler — it will be covered by a text gradient overlay.\n"
        "   - LIGHTING: Dramatic, directional lighting. A single strong key light source (backlit, rim-lit, or "
        "     top-down studio). Deep shadows. Avoid flat, evenly lit scenes.\n"
        "   - NEGATIVE (mention explicitly in the prompt): No text, no UI mockups, no charts, no dashboards, "
        "     no watermarks, no logos, no cluttered backgrounds.\n"
        "   - LENGTH: The image_prompt must be 60-120 words. Be specific and descriptive.\n\n"
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

def draft_reel_script(curated_articles):
    """
    Takes curated articles and drafts a 3-6 slide script for a short-form video (Reel).
    Returns a parsed JSON object containing the slides.
    """
    if not curated_articles:
        return None

    print("Pausing for 15 seconds to respect Gemini Free Tier rate limits...")
    time.sleep(15)

    prompt = (
        "You are an expert short-form video producer (Instagram Reels/TikTok). "
        "Create a fast-paced, highly engaging video script based on the following AI news.\n\n"
        "RULES:\n"
        "- Decide the number of slides (between 3 and 6) based on how complex the story is.\n"
        "- Slide 1 must be a powerful hook.\n"
        "- The narration must be conversational, sharp, and energetic (like a tech YouTuber).\n"
        "- The caption must be an ultra-short (5-10 words maximum) on-screen summary of the narration.\n"
        "- CRITICAL: Inside the caption, wrap the 1 or 2 most important keywords in asterisks (e.g. 'The *future* is here').\n"
        "- The image_prompt must describe a SPECIFIC background for an AI image generator. "\
        "Rules: bold clean digital illustration style (NOT photorealistic), story-specific subject (NOT generic tech), "\
        "strong silhouettes with punchy saturated colors (deep navy, electric teal, amber accents), "\
        "main subject in upper/middle frame (lower 40% used for text overlay), no text, no UI dashboards, no charts, "\
        "simple enough to read on a phone screen, 60-100 words.\n\n"
        "News Developments:\n"
    )

    for article in curated_articles:
        prompt += f"- {article['title']} ({article['source']}): {article['summary']}\n"

    prompt += (
        "\nReturn the result STRICTLY as a valid JSON object following this exact schema:\n"
        "{\n"
        '  "slides": [\n'
        "    {\n"
        '      "narration": "...",\n'
        '      "caption": "...",\n'
        '      "image_prompt": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )

    print("Asking Gemini to draft the Reel script...")
    try:
        response = generate_with_retry(prompt)
        text = extract_text(response).strip()
        
        # Clean up markdown formatting if the LLM wrapped it
        text = text.replace('```json', '').replace('```', '').strip()
        
        # Robust extraction
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
            
        parsed = json.loads(text)
        return parsed
    except Exception as e:
        print(f"Error drafting reel script: {e}")
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
