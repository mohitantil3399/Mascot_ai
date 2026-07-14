# AI Orchestrator (FastAPI + Vision LLM Engine)

Desktop Companion AI Orchestrator backend providing real-time visual streaming, ROI diffing, and multi-provider LLM fallback (`vLLM` / `Ollama` / `OpenAI`).

## Running Locally

To set up the virtual environment and install dependencies:

```powershell
uv venv .venv --python 3.12
uv pip install -e .
```

To run the server:

```powershell
.venv\Scripts\python.exe main.py
```
