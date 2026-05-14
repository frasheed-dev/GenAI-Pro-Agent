import os
import sys

# Add src to python path to make importing clean
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from publishers.make_webhook import post_to_make

def test_webhook():
    print("=== Testing Make.com Webhook ===")
    
    # We will use the image that was successfully generated in your drafts folder
    image_path = os.path.abspath("drafts/news_image_universal.png")
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Could not find image at {image_path}")
        print("Please ensure drafts/news_image_universal.png exists before testing.")
        return
        
    dummy_text = "🚀 This is a test post from the GenAI Pro Agent to verify the Make.com Webhook is working correctly!\n\n#GenAI #Testing"
    
    print(f"Image found: {image_path}")
    print(f"Sending test payload to LinkedIn...")
    
    # Test LinkedIn payload
    linkedin_success = post_to_make(
        platform="linkedin",
        text=dummy_text,
        image_path=image_path
    )
    
    print(f"\nSending test payload to Facebook...")
    
    # Test Facebook payload
    facebook_success = post_to_make(
        platform="facebook",
        text=dummy_text,
        image_path=image_path
    )
    
    if linkedin_success and facebook_success:
        print("\n✅ Both payloads were successfully fired to Make.com!")
        print("Check your Make.com dashboard now!")
    else:
        print("\n❌ Webhook test failed. Check your MAKE_WEBHOOK_URL in .env.")

if __name__ == "__main__":
    test_webhook()
