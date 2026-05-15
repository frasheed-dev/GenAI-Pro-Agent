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
        
    if platform.lower() == "linkedin":
        platform_instructions = "- Keep the tone professional, insightful, and slightly conversational.\n- Keep the total length under 1500 characters."
    elif platform.lower() == "x" or platform.lower() == "twitter":
        platform_instructions = "- Keep it punchy, engaging, and suitable for a Twitter thread format.\n- Ensure it's concise, ideally under 280 characters per thought."
    elif platform.lower() == "facebook":
        platform_instructions = "- Make it engaging for a broader audience, slightly more casual than LinkedIn but still informative.\n- Keep the total length under 1500 characters."
    else:
        platform_instructions = "- Keep it professional and engaging."

    prompt = (
        f"You are a bold, highly opinionated Tech/AI Influencer on {platform.capitalize()}. Write an engaging, highly interactive post "
        "summarizing the following Generative AI news developments.\n\n"
        "CRITICAL FORMATTING RULES:\n"
        "You MUST structure the post EXACTLY into these three sections:\n\n"
        "1️⃣ START WITH A MASSIVE HOOK & KEY TAKEAWAYS (The TL;DR)\n"
        "- Start with a single, punchy, scroll-stopping sentence.\n"
        "- Immediately follow with 2-3 short bullet points summarizing the actual news.\n"
        "- Use relevant emojis for the bullet points to make it visually scannable.\n\n"
        "2️⃣ WHY IT MATTERS (The Influencer Take)\n"
        "- Provide a bold opinion, insider perspective, or edgy commentary on what this news actually means for the industry.\n"
        "- Do not just report the facts—tell them why they should care.\n\n"
        "3️⃣ THE HOOK-AND-HOLD CTA (Drive Comments)\n"
        "- End the post with a thought-provoking, controversial, or highly engaging question to force people to comment. (e.g., 'Are we moving too fast? Drop your thoughts below.')\n\n"
        "ADDITIONAL GUIDELINES:\n"
        "- CRITICAL: Do NOT actually output the section titles/headers (like 'THE TL;DR' or 'WHY IT MATTERS'). Weave these parts naturally into a seamless post.\n"
        "- Do NOT use markdown formatting (like **bold** or *italics*). Social platforms render these as literal asterisks.\n"
        f"{platform_instructions}\n"
        "- Put the Source Links at the very bottom.\n"
        "- Add 3-5 hyper-relevant, niche hashtags at the very end (avoid generic tags like #AI).\n\n"
        "News Developments:\n"
    )
    
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
