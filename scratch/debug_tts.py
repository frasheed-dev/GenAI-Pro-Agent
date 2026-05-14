import asyncio
import edge_tts
import sys

async def debug():
    print("Testing edge-tts Communicate...")
    communicate = edge_tts.Communicate("Hello world, this is a test.", "en-US-JennyNeural")
    try:
        async for chunk in communicate.stream():
            print("Chunk type:", chunk["type"])
            if chunk["type"] == "WordBoundary":
                print("  ->", chunk)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(debug())
