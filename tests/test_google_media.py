import os
import time
import requests
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ Error: GEMINI_API_KEY not found in .env file.")
    exit(1)

# API Endpoints
IMAGEN_URL = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
VEO_URL = f"https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview:predictLongRunning?key={API_KEY}"

def test_nano_banana():
    print("\n--- Testing Google Nano Banana (gemini-2.5-flash-image) ---")
    print("Sending prompt to Nano Banana...")
    
    try:
        import google.generativeai as genai
        import io
        from PIL import Image
        
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        response = model.generate_content('A futuristic glowing robotic fox in a cybernetic forest, photorealistic, 8k resolution')
        
        # Extract inline_data from the response parts
        image_bytes = None
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                image_bytes = part.inline_data.data
                break
                
        if image_bytes:
            os.makedirs("drafts", exist_ok=True)
            with open("drafts/test_nano_banana.png", "wb") as f:
                f.write(image_bytes)
            print("Success! Nano Banana image saved to 'drafts/test_nano_banana.png'")
        else:
            print("Error: Google API succeeded but no image data was found in the response parts.")
            print(response.text)
            
    except Exception as e:
        print(f"Error connecting to Nano Banana: {e}")

def test_veo_video():
    print("\n--- Testing Google Veo (Video Generation) ---")
    print("Initiating long-running video generation task...")
    
    payload = {
        "instances": [
            {
                "prompt": "Cinematic pan of a futuristic glowing robotic fox walking through a neon cybernetic forest, smooth motion"
            }
        ],
        "parameters": {
            "aspectRatio": "16:9"
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(VEO_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        operation_name = data.get("name")
        print(f"Success! Veo operation started. Operation ID: {operation_name}")
        print("Note: Video generation is asynchronous and can take several minutes.")
        print("You would normally poll this operation ID to download the final MP4.")
        
        # We will just do a quick poll to show the user how it works
        poll_url = f"https://generativelanguage.googleapis.com/v1beta/{operation_name}?key={API_KEY}"
        print("Polling status once...")
        time.sleep(2)
        poll_res = requests.get(poll_url)
        print(f"Current Status: {poll_res.json()}")
        
    elif response.status_code == 404:
        print("Error 404: Veo API is not enabled or not available for this API key/region yet.")
        print(response.text)
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    print("Starting Google Media APIs Test...")
    test_nano_banana()
    #test_veo_video()
    print("\nTest complete.")
