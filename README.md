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

### Option A: End-User Installation (PyPI Package) — Recommended ⭐

If you simply want to run Antigravity Desktop Companion right away on your Windows PC without compiling source code, install our official Python package:

```powershell
pip install mascot-ai
```

Once installed, use the `mascot-ai` command anywhere in your terminal:

```powershell
# 1. Configure your API keys interactively (only required once!)
mascot-ai env

# 2. Launch the desktop companion overlay
mascot-ai start
```

That's it! On the first launch, `mascot-ai start` will automatically fetch the visual `.exe` overlay binary from GitHub Releases, start the bundled AI orchestrator (`port 8000`) and UI server (`port 3000`), and launch your desktop companion window.

| Command | Description |
|---|---|
| `mascot-ai env` | Interactive API key setup (stores configuration securely in `~/.mascot-ai/.env`) |
| `mascot-ai env --force` | Re-run key setup anytime |
| `mascot-ai start` | Start all backend and overlay services in one terminal (Ctrl+C to stop all) |
| `mascot-ai status` | Probe active ports and display service health status |

---

### Option B: Developer & Contributor Setup (Source Code)

If you are modifying code across the 3 tiers (FastAPI backend, React UI, or WPF native host):

#### 1. Clone the Repository & Install `mascot` Developer CLI

```powershell
git clone https://github.com/mohitantil3399/Mascot_ai.git
cd Mascot_ai

# One-time install of the developer CLI (`mascot`) into your orchestrator venv:
cd apps/ai-orchestrator
uv pip install -e ../../
.venv\Scripts\Activate.ps1
```

#### 2. Configure Environment & Dependencies

```powershell
# Interactive .env configuration
mascot env

# Install all dependencies across Python, Node.js, and C# (.NET)
mascot install
```

#### 3. Launching Services for Development

```powershell
# Launch all 3 tiers with live combined terminal output
mascot start
```

**Developer CLI (`mascot`) Commands Overview:**

| Command | Description |
|---|---|
| `mascot env` | Interactive local setup — copies `.env.example` to `apps/ai-orchestrator/.env` |
| `mascot install` | Install all dependencies across Python (`uv`), Node (`npm`), and C# (`dotnet`) |
| `mascot install [tier]` | Install specific tier dependencies (`orchestrator`, `ui`, `host`) |
| `mascot start` | Start all 3 tiers in sequence with an 8s delay before the native host |
| `mascot start [tier]` | Start only `orchestrator`, `ui`, or `host` individually |
| `mascot build` | Build production artifacts (`npm run build` + `dotnet publish`) |
| `mascot status` | Probe ports 8000 & 3000 and display service health |


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
