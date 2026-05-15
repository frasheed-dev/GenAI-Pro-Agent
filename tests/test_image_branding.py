import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from core.image_generator import create_news_image

def test_branding():
    print("🎨 Creating visual branding test...")
    
    # We pass a headline containing every letter of the alphabet, wrapped in asterisks so it highlights.
    # We pass a headline containing a contiguous highlighted phrase with mixed descenders to test flush bounding boxes.
    headline = "*status quo* \n*ABCDEFGHIJKLMNOPQRSTUVWXYZ* \n*abcdefghijklmnopqrstuvwxyz*"
    image_prompt = "A simple solid dark blue abstract background"
    
    output_path = "drafts/test_branding.png"
    
    image_path = create_news_image(
        image_prompt=image_prompt, 
        headline=headline, 
        output_path=output_path
    )
    
    if image_path:
        print(f"✅ Test image generated successfully! Open {output_path} to verify the yellow highlight boxes and the new Courier links.")
    else:
        print("❌ Failed to generate test image.")

if __name__ == "__main__":
    test_branding()
