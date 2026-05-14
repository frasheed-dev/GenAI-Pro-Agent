import asyncio
import edge_tts
import json
import sys

async def generate_tts(text, voice, audio_path, json_path):
    communicate = edge_tts.Communicate(text, voice)
    words = []
    
    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "word": chunk["text"],
                    "start": chunk["offset"] / 10000000.0, # convert 100-ns to seconds
                    "end": (chunk["offset"] + chunk["duration"]) / 10000000.0
                })
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"segments": [{"words": words}]}, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python tts_engine.py <text> <voice> <audio_out> <json_out>")
        sys.exit(1)
        
    text = sys.argv[1]
    voice = sys.argv[2]
    audio_path = sys.argv[3]
    json_path = sys.argv[4]
    
    asyncio.run(generate_tts(text, voice, audio_path, json_path))
