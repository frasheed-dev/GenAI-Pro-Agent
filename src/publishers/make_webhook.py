import os
import requests
from dotenv import load_dotenv

load_dotenv()

def post_to_make(platform: str, text: str, image_path: str = None) -> bool:
    """
    Sends the post data (and image file) to a Make.com Webhook.
    Make.com handles the OAuth and native posting to LinkedIn/Facebook.
    """
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ Error: MAKE_WEBHOOK_URL is not defined in .env")
        print("Please create a custom webhook in Make.com and add the URL to your .env file.")
        return False
        
    print(f"📡 Sending payload to Make.com Webhook for {platform}...")
    
    data = {
        "platform": platform.lower(),
        "text": text
    }
    
    files = None
    if image_path and os.path.exists(image_path):
        files = {
            "image": (os.path.basename(image_path), open(image_path, "rb"), "image/png")
        }
        
    try:
        if files:
            # Send as multipart/form-data so the image is uploaded directly to Make.com
            response = requests.post(webhook_url, data=data, files=files)
        else:
            # If no files, just send as standard JSON
            response = requests.post(webhook_url, json=data)
            
        response.raise_for_status()
        print("✅ Successfully triggered Make.com Webhook!")
        return True
    except Exception as e:
        print(f"❌ Failed to send to Make.com: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Response: {response.text}")
        return False
    finally:
        if files:
            files["image"][1].close()
