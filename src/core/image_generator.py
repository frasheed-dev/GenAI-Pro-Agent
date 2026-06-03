import os
import requests
from io import BytesIO
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont, ImageOps

def create_circular_mask(size):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    return mask

def generate_background(prompt, width=1080, height=1350):
    hf_token = os.getenv("HF_TOKEN")
    
    if hf_token:
        print(f"Generating background image via Hugging Face (SDXL) for: {prompt}")
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {hf_token}"}
        # Hugging Face doesn't natively support arbitrary width/height in the free API without custom parameters, 
        # so we rely on the resize() step in create_news_image to fix the aspect ratio.
        payload = {"inputs": prompt}
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
            else:
                print(f"Hugging Face API failed with status {response.status_code}: {response.text}")
                print("Falling back to pollinations.ai...")
        except Exception as e:
            print(f"Hugging Face API connection error: {e}")
            print("Falling back to pollinations.ai...")

    print(f"Generating background image via pollinations.ai for: {prompt}")
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width={width}&height={height}&nologo=true"
    response = requests.get(url)
    
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    elif response.status_code == 402:
        print("❌ Pollinations API Error: 402 Queue Full. This IP is aggressively rate-limited.")
    else:
        print(f"Failed to fetch image from pollinations.ai. Status: {response.status_code}")
        
    return None

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

def draw_highlighted_text(draw, img_width, img_height, headline, font):
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

def create_news_image(image_prompt, headline, output_path="drafts/news_image.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    img = generate_background(image_prompt)
    if not img:
        return None
        
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

def create_slide_image(image_prompt, slide_index, total_slides, output_path):
    """
    Creates a 1080x1920 PNG background for a Reel slide.
    Bakes in the gradient, branding, and slide indicator, but leaves the center/lower-third empty for ffmpeg text.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    img = generate_background(image_prompt, width=1080, height=1920)
    if not img:
        return None
        
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
