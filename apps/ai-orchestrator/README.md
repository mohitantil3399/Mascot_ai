# AI Orchestrator (FastAPI + Vision LLM Engine)

The backend service for Antigravity Desktop Companion. Provides real-time visual streaming, ROI diffing, and a multi-provider LLM fallback chain.

---

## 🔧 Setup

### 1. Install Dependencies

```powershell
# Using uv (recommended):
uv venv .venv --python 3.12
uv pip install -e .
```

```bash
# Or using pip:
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate.bat     # Windows
pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY
```

Get a free Mistral API key at [console.mistral.ai](https://console.mistral.ai).

### 3. Run the Server

```powershell
.venv\Scripts\python.exe main.py
```

The server starts at:
- **Health check**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws

---

## 🌐 API Endpoints

| Endpoint | Type | Description |
|----------|------|-------------|
| `GET /health` | HTTP | Health check — returns `{"status": "ok", "version": "2.0.0"}` |
| `/ws` | WebSocket | Main communication channel for vision prompts and AI responses |

### WebSocket Protocol

The WebSocket uses a binary protocol:

1. **Client → Server** (Text Frame): `{"type": "vision_prompt", "prompt": "..."}`
2. **Client → Server** (Binary Frame): Raw JPEG screenshot bytes
3. **Server → Client** (Text Frames): `{"type": "token", "payload": "..."}` (streamed)

---

## 🤖 LLM Provider Fallback Chain

The engine tries providers in order until one succeeds:

| Priority | Provider | API Key Env Var | Default Model |
|----------|----------|-----------------|---------------|
| 1 | Mistral Pixtral Vision | `MISTRAL_API_KEY` | `pixtral-12b-2409` |
| 2 | OpenRouter | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` |
| 3 | OpenAI GPT-4o | `OPENAI_API_KEY` | `gpt-4o` |

**Local/Offline providers** (LM Studio, Ollama) can be enabled by uncommenting the relevant blocks in `inference/engine.py`. See `.env.example` for the environment variables.

---

## 📁 Structure

```
ai-orchestrator/
├── api/
│   └── ws_endpoint.py        # WebSocket route handler
├── inference/
│   ├── engine.py              # Multi-provider LLM client with fallback
│   ├── prompts.py             # System prompts for the vision model
│   └── vision_parser.py       # ROI crop, Lanczos resize, diff detection
├── main.py                    # FastAPI application entry point
├── test_engine.py             # Engine tests
├── pyproject.toml             # Python project metadata & dependencies
├── .env.example               # Environment variable template
└── uv.lock                    # Locked dependency versions
```

---

## 📦 Dependencies

Key dependencies (see `pyproject.toml` for full list):
- **FastAPI** — Async web framework
- **uvicorn** — ASGI server
- **openai** — OpenAI-compatible client (used for all providers)
- **Pillow** — Image processing (resize, crop)
- **NumPy** — Pixel difference calculations
- **websockets** — WebSocket support
