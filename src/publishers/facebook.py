import os
import requests
from core.config import FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID

def post_to_facebook(text_content, image_path=None):
    """
    Publishes a text or photo post to a Facebook Page via the Graph API.
    """
    if not FACEBOOK_PAGE_ACCESS_TOKEN or not FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ID == "YOUR_FACEBOOK_PAGE_ID_HERE":
        print("FACEBOOK credentials are not correctly set. Please check your .env file.")
        return False
        
    # Remove Markdown bolding since Facebook doesn't support it natively
    text_content = text_content.replace("**", "")
    
    if image_path and os.path.exists(image_path):
        print(f"Uploading photo post to Facebook using image: {image_path}")
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
        payload = {
            "message": text_content,
            "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
        }
        with open(image_path, "rb") as img:
            files = {"source": ("image.png", img, "image/png")}
            response = requests.post(url, data=payload, files=files)
    else:
        print("Warning: No valid image found! Defaulting to a text-only Facebook post.")
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
        payload = {
            "message": text_content,
            "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
        }
        response = requests.post(url, data=payload)
        
    if response.status_code == 200:
        data = response.json()
        print(f"Successfully posted to Facebook! Post ID: {data.get('id')}")
        return True
    else:
        print(f"Failed to post to Facebook. Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
