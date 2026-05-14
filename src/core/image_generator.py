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

def generate_background(prompt):
    print(f"Generating background image for: {prompt}")
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1080&height=1350&nologo=true"
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    print("Failed to fetch image from pollinations.ai")
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
    
    lines = wrap_text(headline, font, img_width - 150)
    
    line_spacing = 40 # Increased spacing to prevent overlap
    dummy_bbox = font.getbbox("A")
    line_height = dummy_bbox[3] - dummy_bbox[1]
    
    total_text_height = (line_height * len(lines)) + (line_spacing * (len(lines) - 1))
    
    current_y = img_height - total_text_height - 180
    
    for line in lines:
        words = line.split(' ')
        clean_line = line.replace('*', '')
        line_width = font.getlength(clean_line)
        current_x = (img_width - line_width) / 2
        
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
                padding_y_top = -10 # Shift the top of the box down
                padding_y_bottom = 30 # Greatly extend the bottom to cover descenders
                
                box_x0 = current_x - padding_x
                box_y0 = current_y - padding_y_top
                box_x1 = current_x + font.getlength(word) + padding_x
                box_y1 = current_y + line_height + padding_y_bottom
                
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
    try:
        font_social = ImageFont.truetype("courbd.ttf", size=24)
        font_icons = ImageFont.truetype(font_awesome_path, size=28)
    except Exception as e:
        print("Could not load Courier New. Using default.")
        font_social = ImageFont.load_default()
        font_icons = ImageFont.load_default()

    CLR_YELLOW = "#F4B41A" 
    CLR_BLUE = "#143d59" 
    
    # --- Top Left Branding (Logo Paste) ---
    # The script is in src/core/, so the root is two directories up
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    logo_path = os.path.join(root_dir, "branding", "final_logo.png")
    
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            
            # Crop out the excess blue square background to tightly hug the circular badge
            logo_w, logo_h = logo.size
            crop_margin = int(logo_w * 0.12)
            logo = logo.crop((crop_margin, crop_margin, logo_w - crop_margin, logo_h - crop_margin))
            
            logo_size = 220 
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            mask = create_circular_mask((logo_size, logo_size))
            logo.putalpha(mask)
            img.paste(logo, (40, 40), logo)
        except Exception as e:
            print(f"Could not paste logo: {e}")
    
    # --- Bottom Social Links ---
    social_y = img_height - 80 # Lifted up slightly
    
    # Facebook
    fb_icon = "\uf09a"
    fb_text = " /genaipro"
    fb_x = 40
    draw.text((fb_x, social_y), fb_icon, font=font_icons, fill=(255, 255, 255, 230))
    draw.text((fb_x + font_icons.getlength(fb_icon), social_y), fb_text, font=font_social, fill=(255, 255, 255, 230))
    
    # LinkedIn
    li_icon = "\uf08c"
    li_text = " /company/genaipro"
    li_width = font_icons.getlength(li_icon) + font_social.getlength(li_text)
    li_x = img_width - li_width - 40
    draw.text((li_x, social_y), li_icon, font=font_icons, fill=(255, 255, 255, 230))
    draw.text((li_x + font_icons.getlength(li_icon), social_y), li_text, font=font_social, fill=(255, 255, 255, 230))

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
