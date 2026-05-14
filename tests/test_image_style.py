import os
import sys

# Add src to python path to make importing clean
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from core.image_generator import create_news_image

def test_vibrant_style():
    print("=== Testing New Vibrant/Cartoonize Aesthetic ===")
    
    # A hardcoded prompt to test the new aesthetic
    test_prompt = "A high-quality 3D cartoonize illustration of a modern technology office, vibrant colors, creative environment, sleek AI robots collaborating on a bright desk, stylish corporate tech illustration"
    test_headline = "AI Startup *Raises $100M* in Funding"
    
    output_path = "drafts/test_vibrant_style.png"
    
    print(f"Sending prompt to Pollinations.ai:\n{test_prompt}\n")
    
    result = create_news_image(test_prompt, test_headline, output_path=output_path)
    
    if result:
        print(f"\n✅ Successfully generated new style image!")
        print(f"Check it out at: {output_path}")
    else:
        print("\n❌ Failed to generate image.")

if __name__ == "__main__":
    test_vibrant_style()
