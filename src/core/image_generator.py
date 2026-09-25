import os
import requests
from io import BytesIO
from urllib.parse import quote
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps

def create_circular_mask(size):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    return mask

def generate_fallback_background(width=1080, height=1350):
    """
    Generates a sleek, high-quality dark-bluish gradient background as a final fallback
    when all AI image generation services (Google, Hugging Face, Pollinations) are unavailable.
    """
    print("🎨 Generating programmatic dark bluish background (Final Fallback)...")
    img = Image.new("RGBA", (width, height), (20, 61, 89, 255))
    draw = ImageDraw.Draw(img)
    
    # Smooth vertical dark navy to deep teal gradient
    top_color = (12, 35, 52)      # Deep Navy
    bottom_color = (25, 75, 105)   # Rich Dark Teal
    
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        
    # Add a subtle radial ambient light glow in the upper-middle region
    glow_center_x, glow_center_y = int(width * 0.5), int(height * 0.35)
    max_radius = int(width * 0.6)
    
    glow_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_overlay)
    
    for r in range(max_radius, 0, -5):
        alpha = int(45 * (1.0 - (r / max_radius)))
        glow_draw.ellipse(
            [glow_center_x - r, glow_center_y - r, glow_center_x + r, glow_center_y + r],
            fill=(40, 115, 155, alpha)
        )
        
    img = Image.alpha_composite(img, glow_overlay)
    return img.convert("RGB")

def generate_background(prompt, width=1080, height=1350, force_fallback=False):
    if force_fallback:
        print("⚡ Force Fallback requested: Skipping AI services and using programmatic dark bluish background.")
        return generate_fallback_background(width, height)

    # Append strict negative text rules to ensure AI image generators never render ghost text in artwork
    negative_suffix = ", flat editorial digital illustration, no text, no words, no letters, no typography, no captions, no watermarks, no titles, no logos"
    clean_prompt = prompt if "no text" in prompt.lower() else f"{prompt}{negative_suffix}"

    together_key = os.getenv("TOGETHER_API_KEY")
    hf_token = os.getenv("HF_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")

    # 1. Primary Method: Google Nano Banana (gemini-2.5-flash-image)
    if gemini_key:
        print(f"Generating background image via Google Nano Banana (gemini-2.5-flash-image) for: {clean_prompt}")
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.5-flash-image')
            response = model.generate_content(clean_prompt)

            # Nano Banana returns content parts, we must extract the inline_data
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    return Image.open(BytesIO(part.inline_data.data))

            print("Google API succeeded but no image data found in response.")
            print("Falling back to Hugging Face Free Space...")
        except Exception as e:
            print(f"Google Nano Banana connection error: {e}")
            print("Falling back to Hugging Face Free Space...")

    # 2. Fallback Method: Gradio Free Space (ZeroGPU)
    try:
        from gradio_client import Client
        print(f"Generating background image via Hugging Face Space (FLUX) for: {clean_prompt}")
        client = Client("KingNish/Realtime-FLUX", token=hf_token)

        result = client.predict(
            prompt=clean_prompt,
            seed=0,
            width=1024,
            height=1024,
            api_name="/generate_image"
        )
        if result and len(result) > 0:
            temp_image_path = result[0]
            return Image.open(temp_image_path)
    except Exception as e:
        print(f"Gradio Space connection error: {e}")
        print("Falling back to Hugging Face SDK...")

    if hf_token:
        print(f"Generating background image via Hugging Face (SDXL) for: {clean_prompt}")
        try:
            # Use the official SDK to handle dynamic routing, endpoints, and DNS issues gracefully
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=hf_token)

            # Text-to-image returns a PIL Image directly
            img = client.text_to_image(clean_prompt, model="stabilityai/stable-diffusion-xl-base-1.0")
            return img
        except Exception as e:
            print(f"Hugging Face API connection error: {e}")
            print("Falling back to pollinations.ai...")

    print(f"Generating background image via pollinations.ai for: {clean_prompt}")
    try:
        url = f"https://image.pollinations.ai/prompt/{quote(clean_prompt)}?width={width}&height={height}&nologo=true"

        pollinations_key = os.getenv("POLLINATIONS_API_KEY")
        if pollinations_key:
            url += f"&key={pollinations_key}"

        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        elif response.status_code == 402:
            print("❌ Pollinations API Error: 402 Queue Full. This IP is aggressively rate-limited.")
        else:
            print(f"Failed to fetch image from pollinations.ai. Status: {response.status_code}")
    except Exception as e:
        print(f"Pollinations API connection error: {e}")

    print("⚠️ ALL AI Image Generators failed (Google, Gradio, HF, Pollinations)!")
    return generate_fallback_background(width, height)

def wrap_text(text, font, max_width):
    lines = []
    words = text.replace('\n', ' \n ').split(' ')
    current_line = []
    
    for word in words:
        if word == '\n':
            lines.append(" ".join(current_line))
            current_line = []
            continue
            
        current_line.append(word)
        clean_line = " ".join(current_line).replace('*', '')
        if font.getlength(clean_line) > max_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def draw_highlighted_text(draw, img_width, img_height, headline, font, start_y=None):
    CLR_PRIMARY = "#F4B41A" 
    CLR_FG_ALT = "#cdcdff" 
    CLR_BG = "#143d59" 
    
    lines = wrap_text(headline, font, img_width - 80)
    
    line_spacing = 20
    dummy_bbox = font.getbbox("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
    text_top = dummy_bbox[1]
    text_bottom = dummy_bbox[3]
    line_height = text_bottom - text_top
    
    total_text_height = (line_height * len(lines)) + (line_spacing * (len(lines) - 1))
    
    if start_y is not None:
        current_y = start_y
    else:
        current_y = img_height - total_text_height - 180
    
    for line in lines:
        words = line.split(' ')
        clean_line = line.replace('*', '')
        line_width = font.getlength(clean_line)
        current_x = (img_width - line_width) / 2
        
        # Pre-calculate the maximum descender for any highlighted word on this line
        # This ensures 'status' and 'quo' have identical flush box heights!
        max_hl_descent = 0
        temp_hl = False
        for w in words:
            if w.startswith('*'): temp_hl = True
            if temp_hl:
                c_w = w.replace('*', '')
                if c_w:
                    max_hl_descent = max(max_hl_descent, font.getbbox(c_w)[3])
            if '*' in w and not w.startswith('*'):
                temp_hl = False
            elif w.startswith('*') and w.endswith('*') and len(w) > 1:
                temp_hl = False
                
        is_highlighted = False
        
        for word in words:
            if not word:
                continue
                
            if word.startswith('*'):
                is_highlighted = True
                word = word[1:]
            
            ends_highlight = False
            if '*' in word:
                ends_highlight = True
                word = word.replace('*', '')
                
            word_width = font.getlength(word + " ")
            
            if is_highlighted:
                padding_x = 10
                padding_y_top = 10
                padding_y_bottom = 10
                
                box_x0 = current_x - padding_x
                box_y0 = current_y + text_top - padding_y_top
                box_x1 = current_x + font.getlength(word) + padding_x
                
                # Use the line's maximum highlighted descender so adjacent words are perfectly flush
                box_y1 = current_y + max_hl_descent + padding_y_bottom
                
                draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill=CLR_PRIMARY)
                draw.text((current_x, current_y), word, font=font, fill=CLR_BG)
            else:
                draw.text((current_x + 3, current_y + 3), word, font=font, fill="black")
                draw.text((current_x, current_y), word, font=font, fill=CLR_FG_ALT)
                
            current_x += word_width
            
            if ends_highlight:
                is_highlighted = False
                
        current_y += line_height + line_spacing

def draw_branding(img, draw, img_width, img_height, font_regular_path, font_awesome_path):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    try:
        # We use the main Roboto font for maximum reliability and cohesive branding
        font_social = ImageFont.truetype(font_regular_path, size=33)
        font_icons = ImageFont.truetype(font_awesome_path, size=38)
    except Exception as e:
        print("Could not load fonts. Using default.")
        font_social = ImageFont.load_default()
        font_icons = ImageFont.load_default()

    CLR_YELLOW = "#F4B41A" 
    CLR_BLUE = "#143d59" 
    
    # --- Top Left Branding (Typographic Circular Badge) ---
    try:
        font_logo = ImageFont.truetype(font_regular_path, size=40)
    except Exception:
        font_logo = ImageFont.load_default()

    brand_x = 40
    brand_y = 40
    
    text_gen = "Gen "
    text_ai = "AI"
    text_pro = "Pro"
    
    # Calculate widths
    w_gen = font_logo.getlength(text_gen)
    w_ai = font_logo.getlength(text_ai)
    w_line1 = w_gen + w_ai
    w_line2 = font_logo.getlength(text_pro)
    
    # Calculate circle diameter to comfortably fit the longest line
    max_w = max(w_line1, w_line2)
    circle_d = int(max_w + 55) # ~27px padding on each side
    
    # Create a separate transparent image for the badge
    badge = Image.new('RGBA', (circle_d, circle_d), (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge)
    
    # Draw semi-transparent black perfect circle
    badge_draw.ellipse([0, 0, circle_d, circle_d], fill=(0, 0, 0, 180))
        
    # Calculate centered Y positions
    total_h = 80 # approx height of two 40px lines
    start_y = (circle_d - total_h) / 2 - 8 # Shift up slightly for font margins
    
    # Draw Line 1: Centered "Gen AI"
    line1_x = (circle_d - w_line1) / 2
    badge_draw.text((line1_x, start_y), text_gen, font=font_logo, fill="#FFFFFF")
    badge_draw.text((line1_x + w_gen, start_y), text_ai, font=font_logo, fill="#F4B41A")
    
    # Draw Line 2: Centered "PRO"
    line2_x = (circle_d - w_line2) / 2
    badge_draw.text((line2_x, start_y + 40), text_pro, font=font_logo, fill="#F4B41A")
    
    # Paste the circular badge onto the main image using itself as the alpha mask
    img.paste(badge, (brand_x, brand_y), badge)
    
    # --- Bottom Social Links ---
    social_y = img_height - 80 # Lifted up slightly
    
    # Facebook (Left)
    fb_icon = "\uf09a"
    fb_text = "/genaipro"
    fb_gap = 12
    fb_x = 40
    draw.text((fb_x, social_y), fb_icon, font=font_icons, fill=(255, 255, 255, 230))
    draw.text((fb_x + font_icons.getlength(fb_icon) + fb_gap, social_y), fb_text, font=font_social, fill=(255, 255, 255, 230))
    
    # Instagram (Center)
    ig_icon = "\uf16d"
    ig_text = "@gen_ai_pro"
    ig_gap = 12
    ig_width = font_icons.getlength(ig_icon) + ig_gap + font_social.getlength(ig_text)
    ig_x = (img_width - ig_width) / 2
    draw.text((ig_x, social_y), ig_icon, font=font_icons, fill=(255, 255, 255, 230))
    draw.text((ig_x + font_icons.getlength(ig_icon) + ig_gap, social_y), ig_text, font=font_social, fill=(255, 255, 255, 230))
    
    # LinkedIn (Right)
    li_icon = "\uf08c"
    li_text = "/company/genaipro"
    li_gap = 12
    li_width = font_icons.getlength(li_icon) + li_gap + font_social.getlength(li_text)
    li_x = img_width - li_width - 40
    draw.text((li_x, social_y), li_icon, font=font_icons, fill=(255, 255, 255, 230))
    draw.text((li_x + font_icons.getlength(li_icon) + li_gap, social_y), li_text, font=font_social, fill=(255, 255, 255, 230))

def create_news_image(image_prompt, headline, output_path="drafts/news_image.png", force_fallback=False):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    img = generate_background(image_prompt, force_fallback=force_fallback)
    if not img:
        img = generate_fallback_background(1080, 1350)
        
    img = img.resize((1080, 1350))
    img = img.convert("RGBA")
    
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    height = img.size[1]
    width = img.size[0]
    
    for y in range(int(height * 0.4), height):
        alpha = int(((y - (height * 0.4)) / (height * 0.6)) * 240)
        draw.line([(0, y), (width, y)], fill=(20, 61, 89, alpha))
        
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    font_path = os.path.join(root_dir, "assets", "fonts", "Roboto-Black.ttf")
    fa_path = os.path.join(root_dir, "assets", "fonts", "fa-brands-400.ttf")
    
    try:
        font = ImageFont.truetype(font_path, size=75)
    except:
        font = ImageFont.load_default()
        
    draw_highlighted_text(draw, width, height, headline, font)
    draw_branding(img, draw, width, height, font_path, fa_path)
    
    img = img.convert("RGB")
    img.save(output_path)
    print(f"Saved generated image to {output_path}")
    return output_path

def create_slide_image(image_prompt, slide_index, total_slides, output_path, force_fallback=False):
    """
    Creates a 1080x1920 PNG background for a Reel slide.
    Bakes in the gradient, branding, and slide indicator, but leaves the center/lower-third empty for ffmpeg text.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    img = generate_background(image_prompt, width=1080, height=1920, force_fallback=force_fallback)
    if not img:
        img = generate_fallback_background(1080, 1920)
        
    img = img.resize((1080, 1920))
    img = img.convert("RGBA")
    
    # Draw dark gradient on bottom half for text readability
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    height = img.size[1]
    width = img.size[0]
    
    for y in range(int(height * 0.5), height):
        alpha = int(((y - (height * 0.5)) / (height * 0.5)) * 240)
        draw.line([(0, y), (width, y)], fill=(20, 61, 89, alpha))
        
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    font_path = os.path.join(root_dir, "assets", "fonts", "Roboto-Black.ttf")
    fa_path = os.path.join(root_dir, "assets", "fonts", "fa-brands-400.ttf")
    
    # Bake in the logo and social icons
    draw_branding(img, draw, width, height, font_path, fa_path)
    
    # Add slide indicator (e.g. "1 / 5") at top right
    try:
        font_indicator = ImageFont.truetype(font_path, size=40)
    except:
        font_indicator = ImageFont.load_default()
        
    indicator_text = f"{slide_index} / {total_slides}"
    ind_w = font_indicator.getlength(indicator_text)
    
    # Draw pill-shaped or rounded rectangle box for the indicator
    pad_x, pad_y = 20, 10
    box_x1 = width - ind_w - (pad_x * 2) - 40
    box_y1 = 40
    box_x2 = width - 40
    box_y2 = 40 + 40 + (pad_y * 2)
    
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=20, fill=(20, 61, 89, 200), outline="#F4B41A", width=3)
    draw.text((box_x1 + pad_x, box_y1 + pad_y), indicator_text, font=font_indicator, fill="#F4B41A")
    
    img = img.convert("RGB")
    img.save(output_path)
    print(f"Saved slide {slide_index}/{total_slides} image to {output_path}")
    return output_path

def draw_slide_indicator(draw, width, slide_index, total_slides, font_path):
    try:
        font_ind = ImageFont.truetype(font_path, size=32)
    except:
        font_ind = ImageFont.load_default()
        
    text = f"{slide_index} / {total_slides}"
    ind_w = font_ind.getlength(text)
    pad_x, pad_y = 18, 8
    box_x1 = width - ind_w - (pad_x * 2) - 40
    box_y1 = 40
    box_x2 = width - 40
    box_y2 = 40 + 32 + (pad_y * 2)
    
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=16, fill=(20, 61, 89, 220), outline="#F4B41A", width=2)
    draw.text((box_x1 + pad_x, box_y1 + pad_y), text, font=font_ind, fill="#F4B41A")

def create_carousel_deck(news_item, output_dir="drafts", force_fallback=False):
    """
    Creates a 3-slide Carousel Deck (1080x1350 PNGs) with a journalistic, objective tone.
      - Slide 1: Cover Card (Headline + Highlight Pointers + Centered/Clean Layout + Swipe -> Indicator)
      - Slide 2: Executive Takeaways (3 Factual Bullet Points, clear of logo badge)
      - Slide 3: Discussion & Growth CTA (Analytical Question + Follow Request, clear of logo badge)
    
    Returns: List of absolute file paths [slide_1_path, slide_2_path, slide_3_path]
    """
    os.makedirs(output_dir, exist_ok=True)
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    font_path = os.path.join(root_dir, "assets", "fonts", "Roboto-Black.ttf")
    fa_path = os.path.join(root_dir, "assets", "fonts", "fa-brands-400.ttf")
    
    headline = news_item.get("headline", "AI Market Intelligence Update")
    prompt = news_item.get("image_prompt", headline)
    category = news_item.get("category", "MARKET INTELLIGENCE").upper()
    bullets = news_item.get("carousel_bullets", [
        "Major developments shaping enterprise AI adoption.",
        "Key shifts in open-source vs. proprietary model capabilities.",
        "Strategic implications for technical leaders and founders."
    ])
    question = news_item.get("discussion_question", "How will this development impact your AI roadmap?")
    
    slide_paths = []
    width, height = 1080, 1350

    # Load fonts
    try:
        font_cat = ImageFont.truetype(font_path, size=28)
        font_head = ImageFont.truetype(font_path, size=64)
        font_swipe = ImageFont.truetype(font_path, size=44)
        font_title = ImageFont.truetype(font_path, size=52)
        font_body = ImageFont.truetype(font_path, size=36)
        font_q_head = ImageFont.truetype(font_path, size=44)
        font_q_body = ImageFont.truetype(font_path, size=52)
        font_cta_head = ImageFont.truetype(font_path, size=36)
        font_cta_sub = ImageFont.truetype(font_path, size=30)
    except:
        font_cat = font_head = font_swipe = font_title = font_body = font_q_head = font_q_body = font_cta_head = font_cta_sub = ImageFont.load_default()

    # ─────────────────────────────────────────────────────────
    # SLIDE 1: Cover Card
    # ─────────────────────────────────────────────────────────
    has_ai_bg = False
    if not force_fallback:
        img1 = generate_background(prompt, width=width, height=height, force_fallback=False)
        if img1:
            has_ai_bg = True

    if not has_ai_bg:
        img1 = generate_fallback_background(width, height)
        
    img1 = img1.resize((width, height)).convert("RGBA")
    
    if has_ai_bg:
        # Bottom gradient overlay for AI artwork
        overlay1 = Image.new('RGBA', img1.size, (0, 0, 0, 0))
        draw1_ov = ImageDraw.Draw(overlay1)
        for y in range(int(height * 0.35), height):
            alpha = int(((y - (height * 0.35)) / (height * 0.65)) * 240)
            draw1_ov.line([(0, y), (width, y)], fill=(20, 61, 89, alpha))
        img1 = Image.alpha_composite(img1, overlay1)
        
    draw1 = ImageDraw.Draw(img1)
    
    # Render branding (logo at top left X=40, Y=40, diameter ~160)
    draw_branding(img1, draw1, width, height, font_path, fa_path)
    
    cat_text = f"  {category}  "
    cat_w = font_cat.getlength(cat_text)
    
    # Swipe prompt styling: "--- SWIPE ---" with clean side accent lines
    swipe_word = "SWIPE"
    swipe_w = font_swipe.getlength(swipe_word)
    swipe_y = height - 160
    
    if not has_ai_bg:
        # FALLBACK MODE: Center headline and category in the middle of canvas
        lines = wrap_text(headline, font_head, width - 120)
        dummy_bbox = font_head.getbbox("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        line_h = dummy_bbox[3] - dummy_bbox[1]
        total_text_h = (line_h * len(lines)) + (20 * (len(lines) - 1))
        
        start_y = (height - total_text_h) / 2
        
        # Category badge centered above headline
        cat_x1 = (width - cat_w - 20) / 2
        cat_y1 = start_y - 90
        draw1.rounded_rectangle([cat_x1, cat_y1, cat_x1 + cat_w + 20, cat_y1 + 50], radius=12, fill=(20, 61, 89, 220), outline="#F4B41A", width=2)
        draw1.text((cat_x1 + 10, cat_y1 + 10), cat_text, font=font_cat, fill="#F4B41A")
        
        # Headline centered
        draw_highlighted_text(draw1, width, height, headline, font_head, start_y=start_y)
        
        # Centered Swipe prompt with vector lines: --- SWIPE ---
        center_x = width / 2
        draw1.text((center_x - (swipe_w / 2), swipe_y), swipe_word, font=font_swipe, fill="#F4B41A")
        
        # Left and Right side accent lines
        line_len = 65
        line_y = swipe_y + 22
        draw1.line([(center_x - (swipe_w / 2) - 25 - line_len, line_y), (center_x - (swipe_w / 2) - 25, line_y)], fill="#F4B41A", width=3)
        draw1.line([(center_x + (swipe_w / 2) + 25, line_y), (center_x + (swipe_w / 2) + 25 + line_len, line_y)], fill="#F4B41A", width=3)
    else:
        # AI ARTWORK MODE: Category badge clear of logo (X=230, Y=55)
        draw1.rounded_rectangle([230, 55, 230 + cat_w + 20, 105], radius=12, fill=(20, 61, 89, 220), outline="#F4B41A", width=2)
        draw1.text((240, 65), cat_text, font=font_cat, fill="#F4B41A")
        
        # Lower third headline
        draw_highlighted_text(draw1, width, height, headline, font_head)
        
        # Swipe prompt bottom right with side lines
        swipe_x = width - swipe_w - 140
        draw1.text((swipe_x, swipe_y), swipe_word, font=font_swipe, fill="#F4B41A")
        line_len = 50
        line_y = swipe_y + 22
        draw1.line([(swipe_x - 15 - line_len, line_y), (swipe_x - 15, line_y)], fill="#F4B41A", width=3)
        draw1.line([(swipe_x + swipe_w + 15, line_y), (swipe_x + swipe_w + 15 + line_len, line_y)], fill="#F4B41A", width=3)

    p1 = os.path.join(output_dir, "carousel_slide_1.png")
    img1.convert("RGB").save(p1)
    slide_paths.append(p1)

    # ─────────────────────────────────────────────────────────
    # SLIDE 2: Executive Takeaways (3 Bullet Points)
    # ─────────────────────────────────────────────────────────
    img2 = generate_fallback_background(width, height).convert("RGBA")
    draw2 = ImageDraw.Draw(img2)
    
    draw_branding(img2, draw2, width, height, font_path, fa_path)
    
    # Header: KEY TAKEAWAYS (Positioned down at Y=240 to clear logo badge!)
    draw2.text((80, 240), "KEY TAKEAWAYS", font=font_title, fill="#FFFFFF")
    draw2.line([(80, 305), (380, 305)], fill="#F4B41A", width=5)
    
    # Draw 3 bullet points starting comfortably below header
    curr_y = 355
    for idx, bullet_text in enumerate(bullets[:3], 1):
        # Yellow bullet marker box
        draw2.rounded_rectangle([80, curr_y + 8, 110, curr_y + 38], radius=6, fill="#F4B41A")
        
        # Wrap bullet text
        b_lines = wrap_text(bullet_text, font_body, width - 200)
        for b_line in b_lines:
            draw2.text((135, curr_y), b_line, font=font_body, fill="#E6EEF4")
            curr_y += 50
        curr_y += 35
        
    p2 = os.path.join(output_dir, "carousel_slide_2.png")
    img2.convert("RGB").save(p2)
    slide_paths.append(p2)

    # ─────────────────────────────────────────────────────────
    # SLIDE 3: Community Discussion & Growth CTA
    # ─────────────────────────────────────────────────────────
    img3 = generate_fallback_background(width, height).convert("RGBA")
    draw3 = ImageDraw.Draw(img3)
    
    draw_branding(img3, draw3, width, height, font_path, fa_path)
    
    # Header: INDUSTRY PERSPECTIVE (Positioned down at Y=240 to clear logo badge!)
    draw3.text((80, 240), "INDUSTRY PERSPECTIVE", font=font_q_head, fill="#A0B2C6")
    draw3.line([(80, 305), (380, 305)], fill="#F4B41A", width=4)
    
    # Discussion Question
    q_lines = wrap_text(question, font_q_body, width - 160)
    q_y = 355
    for q_line in q_lines:
        draw3.text((80, q_y), q_line, font=font_q_body, fill="#F4B41A")
        q_y += 66
        
    # Follow CTA Card Box
    cta_box_y0 = min(q_y + 60, height - 420)
    cta_box_y1 = cta_box_y0 + 250
    draw3.rounded_rectangle([80, cta_box_y0, width - 80, cta_box_y1], radius=24, fill=(15, 45, 68, 240), outline="#F4B41A", width=3)
    
    # CTA Text
    draw3.text((120, cta_box_y0 + 35), "Follow GenAI Pro", font=font_cta_head, fill="#FFFFFF")
    draw3.text((120, cta_box_y0 + 95), "Autonomous daily market intelligence", font=font_cta_sub, fill="#A0B2C6")
    draw3.text((120, cta_box_y0 + 145), "& executive AI analysis.", font=font_cta_sub, fill="#A0B2C6")
    
    # Yellow join button pill
    draw3.rounded_rectangle([width - 320, cta_box_y0 + 165, width - 120, cta_box_y0 + 220], radius=16, fill="#F4B41A")
    draw3.text((width - 290, cta_box_y0 + 177), "+ Follow", font=font_cta_sub, fill="#143D59")

    p3 = os.path.join(output_dir, "carousel_slide_3.png")
    img3.convert("RGB").save(p3)
    slide_paths.append(p3)

    print(f"✅ Saved 3-slide Carousel Deck to {output_dir}/ (carousel_slide_1.png, slide_2.png, slide_3.png)")
    return slide_paths

