import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("NVIDIA_API_KEY")

if not API_KEY:
    print("Error: NVIDIA_API_KEY not found in .env file.")
    exit(1)

# Function to list available models
def list_nvidia_models():
    print("\n--- Fetching Available NVIDIA Models ---")
    url = "https://integrate.api.nvidia.com/v1/models"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        models = data.get("data", [])
        print(f"Successfully fetched {len(models)} models.")
        
        # Filter for models that might be image related
        image_models = [m['id'] for m in models if 'diffusion' in m['id'].lower() or 'image' in m['id'].lower() or 'edify' in m['id'].lower()]
        print("Potential Image Models Available:")
        for m in image_models:
            print(f" - {m}")
        
        return image_models
    else:
        print(f"Error fetching models {response.status_code}: {response.text}")
        return []

# Function to test SDXL Image Generation
def test_nvidia_sdxl():
    print("\n--- Testing NVIDIA Stable Diffusion XL ---")
    
    # Try the standard genai endpoint for SDXL
    invoke_url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-xl"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
    }

    payload = {
        "text_prompts": [
            {
                "text": "A futuristic robotic fox glowing in a cyberpunk city, highly detailed, 8k resolution, cinematic lighting",
                "weight": 1
            }
        ],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30,
    }

    print("Sending prompt to NVIDIA API...")
    response = requests.post(invoke_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        
        # Check if the artifact is returned in base64
        artifacts = data.get("artifacts", [])
        if artifacts:
            os.makedirs("drafts", exist_ok=True)
            b64_image = artifacts[0].get("base64")
            if b64_image:
                with open("drafts/test_nvidia_sdxl.png", "wb") as f:
                    f.write(base64.b64decode(b64_image))
                print("Success! Image saved to 'drafts/test_nvidia_sdxl.png'")
            else:
                print("No base64 data found in the artifacts array.")
        else:
            print("Success response but no artifacts returned.")
            print(data)
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    print("Starting NVIDIA NIM API Test...")
    list_nvidia_models()
    test_nvidia_sdxl()
    print("\nTest complete.")
