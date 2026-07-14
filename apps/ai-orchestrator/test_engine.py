# test_engine.py
# Simple standalone test script to verify LocalLLM vision streaming & fallback behavior.
import asyncio
import io
import sys
from PIL import Image

from inference.engine import LocalLLM, PROVIDERS

async def test_engine():
    print("==========================================")
    print("         Testing LocalLLM Engine          ")
    print("==========================================")
    print(f"Python executable: {sys.executable}")
    print("\n1. Initializing LocalLLM...")
    try:
        llm = LocalLLM()
        print("   -> Successfully initialized LocalLLM.")
    except Exception as e:
        print(f"   -> FAILED to initialize LocalLLM: {e}")
        return False

    for provider, client in zip(PROVIDERS, llm.clients):
        status = "Ready" if client is not None else "Initialization Failed"
        print(f"   - Provider [{provider['name']}]: {status} (base_url: {provider['base_url']})")

    print("\n2. Creating a small 64x64 dummy JPEG image in memory...")
    img = Image.new("RGB", (64, 64), color=(0, 120, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    prompt = "Hello! What color is this image? Reply briefly."
    print(f"\n3. Executing stream_vision() with prompt: '{prompt}'...")
    print("-" * 50)

    token_count = 0
    try:
        async for token in llm.stream_vision(prompt, image_bytes, system_prompt="You are a helpful AI assistant."):
            print(token, end="", flush=True)
            token_count += 1
        print("\n" + "-" * 50)
        print(f"-> Stream completed successfully (Total chunks yielded: {token_count}).")
        return True
    except Exception as e:
        print(f"\n-> Error during streaming: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_engine())
    sys.exit(0 if success else 1)
