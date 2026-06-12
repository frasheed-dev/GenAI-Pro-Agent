import os
import shutil
from gradio_client import Client

def test_gradio_flux():
    print("\n--- Testing Free Hugging Face Gradio Space (FLUX) ---")
    print("Connecting to 'KingNish/Realtime-FLUX' Space...")
    
    try:
        # Connect to the Hugging Face Free ZeroGPU space
        # We can pass an HF token if needed, but many public spaces don't require it
        hf_token = os.getenv("HF_TOKEN")
        client = Client("KingNish/Realtime-FLUX", token=hf_token)
        
        prompt = "A cinematic photo of a glowing neon fox walking through a futuristic city, incredibly detailed, 8k resolution"
        print(f"Sending prompt: '{prompt}'")
        
        # Call the predict endpoint. 
        # Note: The api_name must match the space's exposed endpoint (usually /predict or /generate_image)
        result = client.predict(
            prompt=prompt,
            seed=0,
            width=1024,
            height=1024,
            api_name="/generate_image"
        )
        
        if result and len(result) > 0:
            # Result is usually a tuple where the first element is the temp file path to the generated image
            temp_image_path = result[0]
            
            os.makedirs("drafts", exist_ok=True)
            output_path = "drafts/test_gradio_flux.png"
            
            # Copy from gradio temp directory to our local drafts folder
            shutil.copy(temp_image_path, output_path)
            print(f"Success! Image generated via Gradio and saved to '{output_path}'")
        else:
            print("Error: No valid image returned from the Space.")
            print(result)
            
    except Exception as e:
        print(f"Error connecting or generating via Gradio Space: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_gradio_flux()
