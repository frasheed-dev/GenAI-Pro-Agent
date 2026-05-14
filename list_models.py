import google.generativeai as genai
import os
import sys

# Add src to python path to make importing clean
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from core.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

print("Available text generation models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
