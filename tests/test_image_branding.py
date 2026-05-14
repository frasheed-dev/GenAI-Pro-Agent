import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

def create_circular_mask(size):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    return mask

def draw_new_branding(draw, img_width, img_height, fa_path):
    # Load Roboto for brand, Courier New for social
    try:
        roboto_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Roboto-Black.ttf")
        if not os.path.exists(roboto_path):
            roboto_path = "Roboto-Black.ttf"
            
        font_brand = ImageFont.truetype(roboto_path, size=35) # Size 35 Roboto
        font_social = ImageFont.truetype("courbd.ttf", size=24) # Reduced to 24
        font_icons = ImageFont.truetype(fa_path, size=28) # Reduced to 28
    except Exception as e:
        print("Could not load Courier New. Using default.")
        font_brand = ImageFont.load_default()
        font_social = ImageFont.load_default()
        font_icons = ImageFont.load_default()

    CLR_YELLOW = "#F4B41A" 
    CLR_BLUE = "#143d59" 
    
    # --- Top Left Branding ---
    x_offset = 40
    y_offset = 60
    padding_x = 15
    # Logo Configuration
    logo_size = 120 # Much larger since it represents the entire brand now
    
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


def test_branding():
    print("🎨 Creating visual branding test...")
    
    # Create a solid dark background to mimic a night-time AI image
    img = Image.new("RGB", (1080, 1350), "#2B2B2B")
    draw = ImageDraw.Draw(img)
    
    # Download FontAwesome if needed
    fa_path = "fa-brands-400.ttf"
    if not os.path.exists(fa_path):
        import requests
        r = requests.get("https://github.com/FortAwesome/Font-Awesome/raw/master/webfonts/fa-brands-400.ttf")
        with open(fa_path, "wb") as f: 
            f.write(r.content)
            
    # Apply our new Courier New branding!
    draw_new_branding(draw, 1080, 1350, fa_path)
    
    # Paste circular logo (Now the main watermark)
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "branding", "final_logo.png")
    # Fallback to the concept if final_logo isn't ready
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "branding", "agent_concept_3.png")
        
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        
        # Crop out the excess blue square background to tightly hug the circular badge
        width, height = logo.size
        crop_margin = int(width * 0.12) # Crop 12% off each side (adjust if needed)
        logo = logo.crop((crop_margin, crop_margin, width - crop_margin, height - crop_margin))
        
        logo_size = 220 # Reduced from 280 now that the dead space is removed
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = create_circular_mask((logo_size, logo_size))
        logo.putalpha(mask)
        img.paste(logo, (40, 40), logo)
    
    # Save test image
    os.makedirs("drafts", exist_ok=True)
    out_path = "drafts/test_branding.png"
    img.save(out_path)
    
    print(f"✅ Branding test saved to {out_path}")
    print("Open the image to see the new highlighted 'Generative AI Pro' box and larger Courier New links!")

if __name__ == "__main__":
    test_branding()
