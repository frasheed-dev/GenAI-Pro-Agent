import os
from PIL import Image, ImageDraw, ImageFont

def generate_social_logo():
    print("🎨 Generating high-res social media profile logo...")
    
    # Path handling for tests directory
    root_dir = os.path.dirname(os.path.dirname(__file__))
    out_dir = os.path.join(root_dir, "branding")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "profile_logo.png")
    
    # Load Font
    font_path = os.path.join(root_dir, "assets", "fonts", "Roboto-Black.ttf")
    try:
        font_size = 250
        scale = font_size / 50 # Engine uses size 50, so scale factor is 5
        font = ImageFont.truetype(font_path, size=font_size)
    except:
        print("❌ Font not found.")
        return
        
    text_gen = "Gen "
    text_ai = "AI"
    text_pro = "Pro"
    
    w_gen = font.getlength(text_gen)
    w_ai = font.getlength(text_ai)
    w_line1 = w_gen + w_ai
    w_line2 = font.getlength(text_pro)
    
    # Use exact geometric scale from engine (max_w + 70 scaled up)
    max_w = max(w_line1, w_line2)
    circle_d = int(max_w + (70 * scale))
    
    # Create perfectly sized dynamic canvas
    img = Image.new('RGBA', (circle_d, circle_d), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw solid blackish circle to match the dark branding badge
    draw.ellipse([0, 0, circle_d, circle_d], fill="#0A0A0A")
    
    # Exact geometric Y positioning from engine
    total_h = 100 * scale
    start_y = (circle_d - total_h) / 2 - (10 * scale)
    
    line1_x = (circle_d - w_line1) / 2
    draw.text((line1_x, start_y), text_gen, font=font, fill="#FFFFFF")
    draw.text((line1_x + w_gen, start_y), text_ai, font=font, fill="#F4B41A")
    
    line2_x = (circle_d - w_line2) / 2
    draw.text((line2_x, start_y + (50 * scale)), text_pro, font=font, fill="#F4B41A")
    
    img.save(out_path)
    print(f"✅ Saved geometrically identical high-res profile logo to {out_path}")

if __name__ == "__main__":
    generate_social_logo()
