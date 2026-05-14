import asyncio
import edge_tts
import os

TEXT = "OpenAI just dropped GPT 5.5 Cyber, an incredibly powerful new model designed exclusively to help security researchers patch critical infrastructure."

VOICES = {
    "Guy_Casual_Male": "en-US-GuyNeural",
    "Jenny_Natural_Female": "en-US-JennyNeural",
    "Sonia_British_Female": "en-GB-SoniaNeural",
    "Steffan_Deep_Male": "en-US-SteffanNeural"
}

async def generate_samples():
    os.makedirs('drafts', exist_ok=True)
    print("Generating multiple voice samples...")
    
    for name, voice_id in VOICES.items():
        output_file = f"drafts/voice_sample_{name}.mp3"
        communicate = edge_tts.Communicate(TEXT, voice_id)
        await communicate.save(output_file)
        print(f"✅ Saved: {output_file}")

if __name__ == "__main__":
    asyncio.run(generate_samples())
