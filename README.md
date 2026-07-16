# 🚀 Antigravity Desktop Companion

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![.NET 9](https://img.shields.io/badge/.NET-9.0-purple.svg)](https://dotnet.microsoft.com/download/dotnet/9.0)
[![Python 3.12](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)

An ephemeral, real-time **visual AI assistant** that lives on your Windows desktop as a transparent, click-through overlay. It combines high-performance native screen capture, a 3D animated character with chat UI, and a vision-capable multi-provider AI backend.

---

## ✨ Features

- **Desktop Overlay** — Transparent, always-on-top window with DWM Glass & click-through support
- **3D Animated Mascot** — Soldier character rendered via Three.js / React Three Fiber
- **Real-Time Vision AI** — Captures your screen, sends it to a vision LLM, and streams responses back
- **Multi-Provider Fallback** — Mistral Pixtral → OpenRouter → OpenAI (with optional local LLM support via LM Studio / Ollama)
- **ROI Diffing** — Skips redundant inference when the screen hasn't changed
- **WebSocket Streaming** — Binary protocol for low-latency image + token streaming

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      WINDOWS DESKTOP SHELL                       │
├─────────────────────────────────────────────────────────────────┤
│  C# Native Host (.NET 9 / WPF)                                  │
│  ├── DWM Sheet Glass + Win32 TOPMOST / ToolWindow styles         │
│  ├── Dynamic hit-testing (WM_NCHITTEST)                          │
│  └── Microsoft.Web.WebView2 (IPC Bridge)                         │
│       │                                                          │
│       ├──► React + Three.js UI (Vite SPA)                        │
│       │    ├── 3D Character (Soldier.glb via R3F)                │
│       │    ├── Chat Bubble, Input Bar & Status Pill               │
│       │    └── useNativeBridge / useAIStream hooks                │
│       │                                                          │
│       └──► Screen Capture Pipeline                                │
│            ├── GPU-accelerated capture (ScreenCapture.cs)        │
│            └── ActiveWindowTracker (ROI utility)                 │
│                                                                  │
│       ▼  WebSocket (ws://localhost:8000/ws)                       │
├─────────────────────────────────────────────────────────────────┤
│  Python AI Orchestrator (FastAPI + uvicorn)                       │
│  ├── WebSocket Router (/ws)                                      │
│  ├── Vision Preprocessor (ROI crop, Lanczos, diff threshold)     │
│  └── Multi-Provider LLM Engine (Mistral → OpenRouter → OpenAI)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| **.NET SDK** | 9.0+ | Native Host (WPF) | [dotnet.microsoft.com](https://dotnet.microsoft.com/download/dotnet/9.0) |
| **Python** | 3.12+ | AI Orchestrator | [python.org](https://www.python.org/downloads/) |
| **uv** | Latest | Python env & package manager | `pip install uv` or [docs.astral.sh](https://docs.astral.sh/uv/) |
| **Node.js** | 20+ | UI Frontend (React/Vite) | [nodejs.org](https://nodejs.org/) |
| **npm** | 10+ | Package manager for Node | Bundled with Node.js |

> **Windows only**: The native host tier uses WPF and Win32 APIs, so it requires Windows 10 (build 19041+) or later.

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mohitantil3399/Mascot_ai.git
cd Mascot_ai
```

### 2. Configure Environment

```bash
# Copy the example environment file and add your API key
cp apps/ai-orchestrator/.env.example apps/ai-orchestrator/.env
# Edit .env and set your MISTRAL_API_KEY (free at https://console.mistral.ai)
```

### 3. Start the AI Orchestrator (Tier 1)

```powershell
cd apps/ai-orchestrator
uv venv .venv --python 3.12
uv pip install -e .
.venv\Scripts\python.exe main.py
# Server starts at http://localhost:8000
```

### 4. Start the UI Frontend (Tier 2)

```powershell
cd apps/ui-frontend
npm install
npm run dev
# Dev server starts at http://localhost:3000
```

### 5. Start the Native Host (Tier 3)

```powershell
# Copy and customize the example scripts first:
cp apps/native-host/run_host.ps1.example apps/native-host/run_host.ps1

cd apps/native-host
dotnet build
.\run_host.ps1
```

### One-Click Launch (Optional)

```powershell
# Copy and customize the example launch script:
cp launch_all.bat.example launch_all.bat
# Edit launch_all.bat if needed, then double-click it to start all three tiers.
```

### 🖥️ Developer CLI — `mascot` command

Install the `mascot` CLI once from the repo root and manage the entire project from a single command:

```powershell
# From repo root — one-time install into the orchestrator's venv
cd apps/ai-orchestrator
uv pip install -e ../../   # installs mascot-cli into this venv

# Activate the venv
.venv\Scripts\Activate.ps1

# Now use the mascot command:
mascot --help
```

**Available commands:**

| Command | Description |
|---|---|
| `mascot env` | Interactive first-time setup — copies `.env.example` and prompts for API keys |
| `mascot env --force` | Re-run key setup even if `.env` already exists |
| `mascot install` | Install all dependencies (Python + Node + .NET) |
| `mascot install ui` | Install only Node.js frontend deps |
| `mascot install orchestrator` | Install only Python backend deps |
| `mascot install host` | Restore only .NET native host deps |
| `mascot start` | Start all 3 tiers in one terminal (Ctrl+C to stop all) |
| `mascot start orchestrator` | Start only the Python FastAPI server (port 8000) |
| `mascot start ui` | Start only the Vite dev server (port 3000) |
| `mascot start host` | Build and start only the .NET WPF host |
| `mascot build` | Build production artifacts (UI + dotnet publish) |
| `mascot status` | Probe ports 8000 & 3000 and show a health table |

**Recommended first-run workflow:**
```powershell
mascot env        # set up .env and API keys
mascot install    # install all dependencies
mascot start      # launch everything
```



## 📁 Project Structure

```
Mascot_ai/
├── apps/
│   ├── ai-orchestrator/       # Python FastAPI backend (vision LLM engine)
│   │   ├── api/               # WebSocket endpoint
│   │   ├── inference/         # LLM engine, prompts, vision preprocessing
│   │   ├── main.py            # FastAPI entry point
│   │   ├── .env.example       # Environment template (copy to .env)
│   │   └── pyproject.toml     # Python dependencies
│   │
│   ├── native-host/           # C# WPF desktop overlay (.NET 9)
│   │   ├── NativeInterop/     # Win32 APIs, screen capture, window tracking
│   │   ├── Services/          # WebSocket client, WebView2 bridge
│   │   ├── DesktopCompanion.csproj
│   │   ├── run_host.ps1.example    # Build & run template
│   │   └── sign_build.ps1.example  # Code-signing template
│   │
│   └── ui-frontend/           # React 19 + Three.js UI (Vite)
│       ├── src/
│       │   ├── components/    # Chat bubbles, input bar, 3D pet canvas
│       │   ├── hooks/         # useAIStream, useNativeBridge
│       │   └── main.tsx       # App entry point
│       ├── package.json
│       └── vite.config.ts
│
├── libs/
│   └── shared-types/          # TypeScript protocol definitions
│       └── protocol.ts        # WebSocket & IPC message schemas
│
├── launch_all.bat.example     # One-click launcher template
├── PROJECT_MAP.md             # Detailed architecture documentation
├── CONTRIBUTING.md            # Contributor guidelines
└── LICENSE                    # GPL-3.0
```

---

## 🔧 Configuration

### LLM Provider Fallback Chain

The AI orchestrator tries providers in order until one succeeds:

1. **Mistral Pixtral Vision** (Cloud) — Primary, requires `MISTRAL_API_KEY`
2. **OpenRouter** (Cloud) — Fallback, requires `OPENROUTER_API_KEY`
3. **OpenAI GPT-4o** (Cloud) — Fallback, requires `OPENAI_API_KEY`

For **fully offline** inference, you can enable local providers (LM Studio or Ollama) by uncommenting the relevant sections in `apps/ai-orchestrator/inference/engine.py` and setting the environment variables in your `.env` file.

See [`.env.example`](apps/ai-orchestrator/.env.example) for all available configuration options.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Setting up your development environment
- Code style and commit conventions
- Submitting pull requests

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE) file for details.
