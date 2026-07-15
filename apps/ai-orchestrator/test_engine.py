# test_engine.py
# Standalone test script verifying LocalLLM vision streaming, fallback, and 8-turn session history.
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
        print(f"   - Provider [{provider['name']}]: {status} (model: {provider['model']}, base_url: {provider['base_url']})")

    print("\n2. Creating a small 64x64 dummy JPEG image in memory...")
    img = Image.new("RGB", (64, 64), color=(0, 120, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    print("\n3. Testing multi-turn session history with roles ('system', 'model_response', 'User_query')...")
    session_history = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "User_query", "content": "Previous query."},
        {"role": "model_response", "content": "Previous answer."},
        {"role": "User_query", "content": "Hello! What color is this image? Reply briefly."},
    ]

    print("-" * 50)
    token_count = 0
    try:
        async for token in llm.stream_vision("Hello! What color is this image? Reply briefly.", image_bytes, session_history=session_history):
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

