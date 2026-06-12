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

def test_imagen_3():
    print("\n--- Testing Google Imagen 3 ---")
    print("Sending prompt to Imagen 3...")
    
    payload = {
        "instances": [
            {
                "prompt": "A futuristic glowing robotic fox in a cybernetic forest, photorealistic, 8k resolution"
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1"
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(IMAGEN_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        try:
            # Extract base64 image
            b64_img = data["predictions"][0]["bytesBase64Encoded"]
            os.makedirs("drafts", exist_ok=True)
            with open("drafts/test_imagen3.jpg", "wb") as f:
                f.write(base64.b64decode(b64_img))
            print("Success! Imagen 3 image saved to 'drafts/test_imagen3.jpg'")
        except Exception as e:
            print(f"Error parsing image response: {e}")
            print(data)
    elif response.status_code == 404:
        print("Error 404: Imagen 3 API is not enabled or not available for this API key/region.")
        print(response.text)
    else:
        print(f"Error {response.status_code}: {response.text}")

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
    test_imagen_3()
    test_veo_video()
    print("\nTest complete.")
