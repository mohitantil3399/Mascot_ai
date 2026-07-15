# inference/engine.py
# 2026 Standard: Mistral -> OpenRouter -> OpenAI fallback chain (LM Studio / Ollama in comments)
import base64
import os
import asyncio
from typing import AsyncIterator

from openai import AsyncOpenAI
from PIL import Image

# Simple zero-dependency .env file loader so environment variables are loaded automatically
def _load_env_files():
    for env_path in [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"),
        ".env",
    ]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k and k not in os.environ:
                                os.environ[k] = v
            except Exception as e:
                print(f"[Engine] Note: Could not parse {env_path}: {e}")

_load_env_files()

# Provider configuration — ordered by preference. Base URLs/models are
# overridable via env vars so this works on any machine.
PROVIDERS = [
    # -------------------------------------------------------------------------
    # Offline / Local LLM support (commented out by default).
    # To enable local offline inference via LM Studio or Ollama, uncomment
    # the dictionary entries below and ensure the local server is running.
    # -------------------------------------------------------------------------
    # {
    #     "name": "LM Studio (localhost Qwen2.5-VL)",
    #     "base_url": os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
    #     "api_key": "local",
    #     "model": os.environ.get("LMSTUDIO_MODEL", "qwen2.5-vl-3b-instruct"),
    # },
    # {
    #     "name": "Ollama (local CPU/GPU fallback)",
    #     "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    #     "api_key": "local",
    #     "model": os.environ.get("OLLAMA_MODEL", "llava"),
    # },
    # -------------------------------------------------------------------------
    # External Cloud API Stack (Supported Natively)
    # -------------------------------------------------------------------------
    {
        "name": "Mistral Pixtral Vision (Cloud API)",
        "base_url": os.environ.get("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
        "api_key": os.environ.get("MISTRAL_API_KEY") or os.environ.get("mistral_api_key") or "missing-key",
        "model": os.environ.get("MISTRAL_MODEL", "pixtral-12b-2409"),
    },
    {
        "name": "OpenRouter Vision API",
        "base_url": os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "api_key": os.environ.get("OPENROUTER_API_KEY") or os.environ.get("openrouter_api_key") or "missing-key",
        "model": os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    },
    {
        "name": "OpenAI GPT-4o (Cloud API)",
        "base_url": os.environ.get("OPENAI_BASE_URL") or None,  # Uses default OpenAI base URL
        "api_key": os.environ.get("OPENAI_API_KEY") or "dummy-key",
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
    },
]

class LocalLLM:
    """Multi-provider LLM engine with automatic fallback chain."""

    def __init__(self):
        self.clients = []
        for p in PROVIDERS:
            try:
                client = AsyncOpenAI(
                    base_url=p.get("base_url") or None,
                    api_key=p.get("api_key") or "dummy-key",
                    timeout=30.0,
                )
                self.clients.append(client)
            except Exception as e:
                print(f"[Engine] Failed to initialize client for '{p.get('name')}': {e}")
                self.clients.append(None)

    @staticmethod
    def _to_base64(image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    async def stream_vision(
        self,
        prompt: str,
        image_bytes: bytes,
        system_prompt: str = "",
        session_history: list[dict] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream vision response with automatic provider fallback and multi-turn session context.
        session_history uses dictionaries with roles: 'system', 'model_response', and 'User_query'.
        """
        b64_image = self._to_base64(image_bytes)

        # If no session history is passed, build a temporary single-turn history
        if session_history is None:
            session_history = []
            if system_prompt:
                session_history.append({"role": "system", "content": system_prompt})
            session_history.append({"role": "User_query", "content": prompt})

        # Convert session dictionary format ('system', 'model_response', 'User_query')
        # into standard OpenAI format ('system', 'assistant', 'user')
        # Find the index of the most recent User_query so only that turn receives the image block,
        # keeping all previous historical turns strictly text-only to prevent token bloat.
        last_user_idx = -1
        for idx in range(len(session_history) - 1, -1, -1):
            if session_history[idx].get("role") == "User_query":
                last_user_idx = idx
                break

        messages = []
        for idx, entry in enumerate(session_history):
            role_map = {
                "system": "system",
                "model_response": "assistant",
                "User_query": "user",
            }
            mapped_role = role_map.get(entry.get("role"), "user")
            content = entry.get("content", "")

            # Attach image_url strictly only to the most recent User_query
            if idx == last_user_idx and image_bytes:
                messages.append({
                    "role": mapped_role,
                    "content": [
                        {"type": "text", "text": str(content)},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
                    ],
                })
            else:
                messages.append({
                    "role": mapped_role,
                    "content": str(content),
                })

        for i, (client, provider) in enumerate(zip(self.clients, PROVIDERS)):
            try:
                if client is None:
                    raise RuntimeError(f"Client for provider '{provider.get('name')}' failed to initialize.")
                print(f"[Engine] Attempting inference via provider: {provider['name']} (model: {provider['model']})")
                response = await client.chat.completions.create(
                    model=provider["model"],
                    messages=messages,
                    stream=True,
                    max_tokens=2048,
                    temperature=0.7,
                )
                async for chunk in response:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                return  # Success — exit after first working provider

            except Exception as e:
                print(f"[Engine] Provider '{provider['name']}' failed: {e}")
                if i == len(PROVIDERS) - 1:
                    yield f"\n\n[System Note] Local & cloud inference fallback triggered. (Last error: {e})"
                    return
                print(f"[Engine] Automatic fallback to next provider...")
                await asyncio.sleep(0.1)

