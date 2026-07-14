# Project Overview

**Antigravity Desktop Companion** is an ephemeral, real-time visual AI assistant designed to live on the Windows desktop as a transparent, click-through overlay. It combines high-performance native Windows screen capture (.NET 9 WPF + DWM Sheet Glass), a 3D animated character and chat UI (React 19 + Three.js / R3F + WebGPU), and a vision-capable multi-provider AI backend (Python FastAPI + vLLM/Ollama/OpenAI).

Unlike traditional chat assistants, Antigravity Desktop Companion operates statelessly across sessions: when a user asks a question, the native C# host captures the current primary monitor (or Region of Interest), encodes it directly into binary JPEG bytes, and streams both metadata and image binary frames over a persistent WebSocket connection (`ws://localhost:8000/ws`) to the Python orchestrator. The AI orchestrator checks for visual differences (`VisionPreprocessor`) to skip redundant inference, runs the vision prompt through a prioritized local/cloud LLM fallback chain, and streams real-time token chunks back to the 3D character and chat UI inside the `WebView2` container.

---

# Architecture Diagram (text format)

```
====================================================================================================
                                      WINDOWS DESKTOP SHELL
====================================================================================================
  [ C# Native Host (.NET 9 / WPF Window) ]
  |-- Configured with DWM Sheet Glass & Win32 TOPMOST / ToolWindow styles
  |-- Dynamic hit-testing (WM_NCHITTEST) routes clicks between UI and background pass-through
  |
  |=== Microsoft.Web.WebView2 (IPC Bridge via PostWebMessageAsJson / WebMessageReceived) ===|
  |                                                                                         |
  v                                                                                         v
[ React + Three.js UI (Vite SPA) ]                                      [ Screen Capture Pipeline ]
  |-- 3D Character Rendering (Soldier.glb via R3F / WebGPU)                 |-- GpuScreenCapture (ScreenCapture.cs)
  |-- Chat Bubble, Input Bar & Connection Status Pill                       |-- Downscales capture to max 1024px
  |-- useNativeBridge / useAIStream state management                        |-- ActiveWindowTracker (ROI utility)
  |                                                                                         |
  +-------------------------------------+---------------------------------------------------+
                                        |
                                        | Persistent WebSocket Connection (ws://localhost:8000/ws)
                                        | Binary Protocol:
                                        |   1. Text JSON Metadata Frame: {"type": "vision_prompt", "prompt": "..."}
                                        |   2. Binary JPEG Frame: <raw image bytes>
                                        |   3. Streamed Text Token Frames: {"type": "token", "payload": "..."}
                                        v
====================================================================================================
                                  PYTHON AI ORCHESTRATOR SERVICE
====================================================================================================
  [ FastAPI Server (main.py + uvicorn) ]
  |
  +--> [ WebSocket Router (/ws) ] (api/ws_endpoint.py)
         |
         +--> [ Vision Preprocessor ] (inference/vision_parser.py)
         |      |-- Crops to Region of Interest (ROI bounds [x, y, w, h] if provided)
         |      |-- Downscales via Lanczos resampling (max 1024px)
         |      |-- Calculates normalized mean RGB pixel difference vs last frame (threshold 0.05)
         |
         +--> [ Multi-Provider LocalLLM Engine ] (inference/engine.py + inference/prompts.py)
                |-- Fallback Chain (ordered by priority):
                      1. LM Studio (Localhost Qwen2.5-VL via http://localhost:1234/v1)
                      2. Ollama (Local CPU/GPU fallback via http://localhost:11434/v1)
                      3. OpenAI GPT-4o (Cloud fallback via OPENAI_API_KEY)
                |-- Streams tokens back over open WebSocket to C# Host / React UI
```

---

# Technology Stack

- **Languages**: C# 13 (.NET 9), Python 3.12, TypeScript 5.8, HTML5/Vanilla CSS
- **Frameworks**:
  - **Backend (.NET)**: WPF (Windows Presentation Foundation), `Microsoft.Web.WebView2` (v1.0.2651.64), Win32 P/Invoke (`user32.dll`, `dwmapi.dll`)
  - **Backend (Python)**: FastAPI (v0.111.0+), Uvicorn (v0.30.0+), OpenAI Async Python SDK (v1.35.0+), Pillow (v10.3.0+), NumPy (v1.26.0+)
  - **Frontend (Web)**: React 19 (`react`, `react-dom`), Three.js (`three` v0.171.0+), React Three Fiber (`@react-three/fiber` v9.0.0+), React Three Drei (`@react-three/drei` v10.0.0+)
- **Runtime Versions**:
  - `.NET SDK`: 9.0.314 (pinned via `apps/native-host/global.json`)
  - `Python`: 3.10+ (recommend 3.12 managed via `uv`)
  - `Node.js`: 18.x / 20.x+ (ESNext target)
- **Package Managers**:
  - `.NET`: NuGet (managed via `.csproj`)
  - `Python`: `uv` (`uv pip` / `pyproject.toml` / `uv.lock`)
  - `Frontend`: `npm` (`package.json` / `package-lock.json`)
- **Build Tools**:
  - `.NET`: `dotnet build` / `MSBuild`
  - `Python`: `setuptools` build backend
  - `Frontend`: `vite` v6.0.0+ (`tsc && vite build`)

---

# Repository Structure

### `/apps/ai-orchestrator`
- **Purpose**: Python/FastAPI backend service responsible for WebSocket communication, image preprocessing, ROI cropping/diffing, and multi-provider LLM vision streaming.
- **Important files**:
  - `main.py`: FastAPI server configuration, CORS middleware, and WebSocket route registration (`/ws`).
  - `api/ws_endpoint.py`: Asynchronous WebSocket endpoint processing binary frames and managing cancellation tasks.
  - `inference/engine.py`: `LocalLLM` engine class managing async connections to LM Studio, Ollama, and OpenAI API endpoints.
  - `inference/vision_parser.py`: `VisionPreprocessor` class handling cropping, Lanczos downscaling, and `ImageChops` frame differencing.
  - `inference/prompts.py`: Defines `SYSTEM_PROMPT` establishing the Antigravity Companion persona.
  - `pyproject.toml` & `uv.lock`: Dependency specification and exact lockfile.
- **Do not modify unless**: Changing AI inference behavior, adding/adjusting LLM fallback providers, modifying image preprocessing thresholds, or updating WebSocket endpoints.

### `/apps/native-host`
- **Purpose**: C# .NET 9 WPF desktop shell that renders the transparent overlay window, bridges `WebView2` with the desktop shell, and executes high-speed screen captures.
- **Important files**:
  - `DesktopCompanion.csproj` & `global.json`: Project settings and .NET SDK version pinning.
  - `MainWindow.xaml` & `MainWindow.xaml.cs`: Core window setup, `WM_NCHITTEST` Win32 message hook for click routing, and `WebView2` initialization.
  - `NativeInterop/WindowManagement.cs`: P/Invoke declarations configuring DWM sheet glass (`DwmExtendFrameIntoClientArea`), Win32 `TOPMOST` Z-order, and tool window style.
  - `NativeInterop/ScreenCapture.cs`: `GpuScreenCapture` class executing screen capture and aspect-ratio preserving JPEG downscaling.
  - `NativeInterop/ActiveWindowTracker.cs`: Win32 P/Invoke utility querying foreground application window bounds (`RECT`) for ROI cropping.
  - `Services/AIWebSocketClient.cs`: Persistent `ClientWebSocket` service with exponential backoff and binary frame dispatching.
  - `Services/WebViewBridge.cs`: Strongly typed JSON bridge (`PostWebMessageAsJson` / `WebMessageReceived`) between WPF host and React UI.
  - `run_host.ps1`: PowerShell helper script invoking the exact .NET SDK path.
- **Do not modify unless**: Adjusting window transparency/hit-testing coordinates, changing screen capture mechanics, or updating IPC/WebSocket wire transport layers.

### `/apps/ui-frontend`
- **Purpose**: Single-page web application (React 19 + TypeScript + Vite + R3F) rendered inside `WebView2` (or browser) displaying the 3D pet and chat interface.
- **Important files**:
  - `vite.config.ts` & `package.json`: Build pipeline configuration (configured to bundle `.glb` 3D assets).
  - `index.html` & `src/main.tsx`: DOM entry points.
  - `src/App.tsx`: Main React component orchestrating pet states (`idle`, `thinking`, `talking`), chat visibility, and connection status.
  - `src/index.css`: Vanilla CSS design system with HSL dark glassmorphism tokens and micro-animations.
  - `src/hooks/useNativeBridge.ts`: Custom hook abstracting bidirectional communication (`postMessage`) with the C# host (with standalone browser fallback using HTML5 Screen Capture API).
  - `src/hooks/useAIStream.ts`: Custom hook managing streamed AI text chunks and state ref accumulation.
  - `src/components/pet/PetCanvas.tsx` & `PetModel.tsx`: Three.js / R3F canvas and character model (`Soldier.glb`) with state-driven animation loops (`Idle`, `Walk`, `Run`).
  - `src/components/chat/ChatBubble.tsx` & `InputBar.tsx`: Interactive chat UI components.
  - `src/types/ipc.d.ts`: TypeScript type definitions for native window objects and IPC message schemas.
- **Do not modify unless**: Updating UI layouts, modifying 3D animations/models, adding frontend chat features, or altering React bridge state logic.

### `/libs/shared-types`
- **Purpose**: Standalone reference folder containing `protocol.ts`, documenting unified TypeScript schemas for WebSocket (`WebSocketClientMessage`, `WebSocketServerMessage`) and IPC (`IpcToHostMessage`, `IpcToUiMessage`) messages across tiers.
- **Important files**: `protocol.ts`.
- **Do not modify unless**: Updating the canonical wire protocol schemas across the application tiers.

---

# Application Flow

1. **User Action Starts Here**:
   - The user types a question into the React `InputBar` or clicks the `📸 Share Screenshot & Analyze` button (`App.tsx`).
2. **Frontend Processes Request**:
   - `App.tsx` sets `petState` to `'thinking'`, opens the chat panel, and invokes `postToNative({ type: 'capture_and_ask', prompt })` via `useNativeBridge.ts`.
3. **IPC Request Goes to Native Service**:
   - Inside `WebView2`, `window.chrome.webview.postMessage` sends the JSON string to the C# WPF Host (`MainWindow.xaml.cs`).
   - `WebViewBridge` intercepts the message via `WebMessageReceived` and dispatches it to `MainWindow`.
4. **Backend C# Logic & Screen Capture Execute**:
   - `MainWindow` invokes `_capture.CapturePrimaryScreenJpeg(1024)` (`ScreenCapture.cs`), downscaling the primary monitor to a 1024px max dimension binary JPEG.
   - Immediately after capture, C# sends `{ "type": "capture_complete" }` back to React (`WebViewBridge.SendCaptureCompleteAsync()`), and `_wsClient` (`AIWebSocketClient.cs`) transmits two consecutive WebSocket frames to `ws://localhost:8000/ws`:
     1. **Text Frame**: `{"type": "vision_prompt", "prompt": "..."}`
     2. **Binary Frame**: Raw `byte[]` JPEG array.
5. **Python Orchestrator & AI Inference Interaction**:
   - `ws_endpoint.py` (`websocket_endpoint`) receives the text metadata and binary image frames.
   - `VisionPreprocessor.process_and_check_diff` (`vision_parser.py`) crops to ROI (if provided), downscales, and compares mean RGB pixel differences against `_last_processed_frame`. If `has_changed` is false and the prompt is empty, it returns a static screen notification to save VRAM.
   - If inference is required, `LocalLLM.stream_vision` (`engine.py`) formats the image as a base64 data URL and queries the providers in sequence (`LM Studio` $\rightarrow$ `Ollama` $\rightarrow$ `OpenAI`).
6. **Response Returns & Real-time UI Streaming**:
   - As each token chunk arrives from the LLM, `ws_endpoint.py` sends a JSON text frame `{"type": "token", "payload": chunk}` over the WebSocket.
   - `AIWebSocketClient.ListenAsync()` (`AIWebSocketClient.cs`) reads the frame and calls `WebViewBridge.DispatchAIChunkAsync(payload)`.
   - `WebViewBridge` executes `_webView.PostWebMessageAsJson(msg)` sending `{"type": "ai_chunk", "payload": chunk}` to the React application.
   - `useNativeBridge.ts` receives the DOM event, triggers `App.tsx` (`handleNativeMessage`), sets `petState` to `'talking'`, and appends the text to `ChatBubble.tsx` via `useAIStream.ts`. When `stream_end` arrives, the pet returns to `'idle'`.

---

# File Responsibility Map

| File | Purpose | Inputs | Outputs | Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| `launch_all.bat` | Orchestration script launching all 3 project tiers in separate terminal windows. | User execution (`double-click`) | Launches AI Orchestrator, UI Frontend, and Native Host | `cmd.exe`, `powershell.exe`, `python`, `npm`, `dotnet` |
| `apps/ai-orchestrator/main.py` | FastAPI entry point configuring CORS, `/health`, and `/ws` WebSocket route. | HTTP/WebSocket requests | `FastAPI` application instance | `fastapi`, `uvicorn`, `api.ws_endpoint` |
| `apps/ai-orchestrator/api/ws_endpoint.py` | Asynchronous WebSocket handler processing binary image frames and token streaming. | WebSocket text (JSON) & binary (JPEG) frames | Streamed JSON (`stream_start`, `token`, `stream_end`) | `inference.engine`, `inference.vision_parser`, `inference.prompts` |
| `apps/ai-orchestrator/inference/engine.py` | `LocalLLM` engine class implementing multi-provider async chat completion fallback. | Prompt string, raw JPEG bytes, system prompt | `AsyncIterator[str]` token chunks | `openai`, `PROVIDERS` config |
| `apps/ai-orchestrator/inference/vision_parser.py` | `VisionPreprocessor` performing ROI cropping, Lanczos resizing, and pixel diffing. | Raw JPEG bytes, ROI coordinates | Tuple of `(processed_jpeg_bytes, has_changed)` | `PIL.Image`, `PIL.ImageChops`, `numpy` |
| `apps/ai-orchestrator/inference/prompts.py` | Contains `SYSTEM_PROMPT` string defining assistant persona and behavior. | None | `SYSTEM_PROMPT` string | None |
| `apps/native-host/DesktopCompanion.csproj` | .NET 9 WPF build configuration and package references (`WebView2`, `System.Drawing.Common`). | `dotnet build` | C# Windows Executable (`DesktopCompanion.exe`) | .NET 9 SDK |
| `apps/native-host/MainWindow.xaml.cs` | Main WPF Window handling `WM_NCHITTEST` hit-testing, `WebView2` setup, and event routing. | Win32 mouse events, React IPC messages | Transparent window overlay, screen capture requests | `NativeInterop.*`, `Services.*`, `Microsoft.Web.WebView2` |
| `apps/native-host/NativeInterop/WindowManagement.cs` | Win32 P/Invoke bridge configuring DWM sheet glass and `TOPMOST` layered behavior. | WPF `Window` handle | Win32 API calls (`SetWindowPos`, `DwmExtendFrameIntoClientArea`) | `user32.dll`, `dwmapi.dll` |
| `apps/native-host/NativeInterop/ScreenCapture.cs` | `GpuScreenCapture` class capturing primary screen via GDI+ and downscaling to JPEG. | Screen capture request (`maxDimension`) | `byte[]` JPEG array | `System.Drawing`, `System.Drawing.Imaging` |
| `apps/native-host/NativeInterop/ActiveWindowTracker.cs` | Win32 P/Invoke utility querying active foreground application rectangle (`RECT`). | Foreground window handle | `System.Drawing.Rectangle` bounding box | `user32.dll` |
| `apps/native-host/Services/AIWebSocketClient.cs` | Persistent WebSocket client maintaining connection to Python backend with retry backoff. | Vision prompts, binary JPEG arrays | WebSocket transmission, dispatched JSON chunks | `System.Net.WebSockets`, `WebViewBridge` |
| `apps/native-host/Services/WebViewBridge.cs` | Typed bridge sending/receiving JSON between C# WPF host and `WebView2` React UI. | Token strings, status updates, React JSON messages | `_webView.PostWebMessageAsJson()` | `Microsoft.Web.WebView2.Core` |
| `apps/ui-frontend/vite.config.ts` | Vite configuration bundling React SPA and `.glb`/`.gltf` 3D assets (`port: 3000`). | Frontend source code | Production bundle (`/dist`) or dev server | `vite`, `@vitejs/plugin-react` |
| `apps/ui-frontend/src/App.tsx` | Root React component managing character animation state, chat panel, and connection status. | User clicks, native IPC messages | Rendered DOM & 3D character overlay | `useNativeBridge`, `useAIStream`, `PetCanvas`, `ChatBubble` |
| `apps/ui-frontend/src/hooks/useNativeBridge.ts` | React custom hook providing unified `postToNative` API across C# host and standalone browser. | Message handler callback, outbound React messages | `window.chrome.webview.postMessage` or direct `WebSocket` | `types/ipc.d.ts` |
| `apps/ui-frontend/src/hooks/useAIStream.ts` | React custom hook accumulating streamed token chunks into reactive state. | `startStream()`, `appendChunk()`, `endStream()` | `{ response, isStreaming, ... }` state | `react` (`useState`, `useCallback`, `useRef`) |
| `apps/ui-frontend/src/components/pet/PetCanvas.tsx` | R3F `Canvas` wrapper configuring lights, WebGPU renderer, and floating animation. | `animState` (`idle` \| `thinking` \| `talking`) | Three.js / WebGPU 3D scene | `@react-three/fiber`, `@react-three/drei`, `PetModel` |
| `apps/ui-frontend/src/components/pet/PetModel.tsx` | R3F character model loader (`Soldier.glb`) orchestrating animation cross-fading. | `animState` (`idle` \| `thinking` \| `talking`) | Rendered 3D character mesh with orbiting ring | `three`, `@react-three/drei` (`useGLTF`, `useAnimations`) |
| `apps/ui-frontend/src/components/chat/ChatBubble.tsx` | Chat viewport component rendering auto-scrolling AI responses and streaming cursor. | `response` string, `isStreaming` boolean | Formatted chat bubble DOM | `react` |
| `apps/ui-frontend/src/components/chat/InputBar.tsx` | User input bar component supporting enter key submission and disabled states. | `onSend(prompt)` callback, `disabled` boolean | Input text box & send button DOM | `react` |
| `apps/ui-frontend/src/index.css` | Design system stylesheet defining HSL glassmorphism tokens, animations, and transparency. | None | Applied visual CSS styles | None |
| `libs/shared-types/protocol.ts` | Canonical TypeScript schema definitions for WebSocket and WebView2 IPC messages across tiers. | None | Exported TypeScript types (`WebSocketClientMessage`, etc.) | None |

---

# Backend (.NET) Guide

- **Projects**: Single WPF application project (`apps/native-host/DesktopCompanion.csproj`) targeting `net9.0-windows10.0.19041.0`.
- **Entry Points**: Standard WPF lifecycle defined in `App.xaml` / `App.xaml.cs`, which launches `MainWindow.xaml` (`MainWindow.xaml.cs`).
- **Controllers / Windows**: `MainWindow.xaml.cs` acts as the primary controller and view container. It overrides `OnSourceInitialized` to install a Win32 message hook (`WndProc`) intercepting `WM_NCHITTEST` (0x0084). By evaluating `screenX` and `screenY` against the status pill, pet container, and chat panel rectangles, it returns `HTCLIENT` for interactive UI elements and `HTTRANSPARENT` (-1) for background space.
- **Services**:
  - `WebViewBridge` (`Services/WebViewBridge.cs`): Wraps `CoreWebView2` to send strongly typed JSON messages (`PostWebMessageAsJson`) and subscribe to incoming web messages (`WebMessageReceived`).
  - `AIWebSocketClient` (`Services/AIWebSocketClient.cs`): Implements `ClientWebSocket` connecting to `ws://localhost:8000/ws`. Maintains background listening (`ListenAsync`), automatic reconnection with exponential backoff (`reconnectAttempts`), and binary frame dispatching.
- **Models**: Uses C# anonymous types serialized via `System.Text.Json.JsonSerializer` for IPC payloads (`new { type = "ai_chunk", payload = ... }`).
- **Dependency Injection**: Services (`_bridge`, `_wsClient`, `_capture`) are instantiated directly within `MainWindow` class state, avoiding heavy DI container overhead for low-latency desktop execution.
- **Configuration**: Uses `DesktopCompanion.csproj` and `global.json` for SDK pinning (`9.0.314`). The backend WebSocket URL defaults to `ws://localhost:8000/ws` (`AIWebSocketClient.cs`).
- **Database Access / Native Interop**: Stateless (no database required). Native Win32 integration is organized under `NativeInterop/`:
  - `WindowManagement.cs`: Configures DWM sheet glass (`DwmExtendFrameIntoClientArea`) and `SetWindowPos` (`HWND_TOPMOST`).
  - `ScreenCapture.cs`: Captures primary monitor screen bitmaps and downscales them to JPEG (`CapturePrimaryScreenJpeg`).
  - `ActiveWindowTracker.cs`: Win32 foreground window bounds utility (`GetActiveAppBounds`).

---

# Python/FastAPI Guide

- **Application Entry Point**: `apps/ai-orchestrator/main.py` initializes the `FastAPI` application (`version="2.0.0"`), registers `CORSMiddleware`, defines `/health`, and mounts the `/ws` WebSocket endpoint before starting the `uvicorn` ASGI server (`port=8000`).
- **Routers / Endpoints**:
  - `GET /health`: Returns JSON `{"status": "ok", "version": "2.0.0"}`.
  - `WEBSOCKET /ws`: Handled by `websocket_endpoint` inside `api/ws_endpoint.py`.
- **Schemas**: Wire protocol uses JSON text frames for metadata (`{"type": "vision_prompt", "prompt": str, "roi": list[int]}`) and streaming token output (`{"type": "token", "payload": str}`).
- **Services / Engines**:
  - `LocalLLM` (`inference/engine.py`): Multi-provider inference engine. On initialization, it instantiates `AsyncOpenAI` clients for all `PROVIDERS`. When `stream_vision()` is called, it iterates through providers in order:
    1. `LM Studio` (`http://localhost:1234/v1`, model: `qwen2.5-vl-3b-instruct`)
    2. `Ollama` (`http://localhost:11434/v1`, model: `llava`)
    3. `OpenAI` (cloud base URL, model: `gpt-4o`)
  - `VisionPreprocessor` (`inference/vision_parser.py`): Preprocessing pipeline that crops incoming binary JPEG bytes to `roi_bounds` if present, downscales via `Image.LANCZOS` (`max_dimension=1024`), and computes mean RGB pixel differences (`diff_threshold=0.05`) against `_last_processed_frame`.
- **Dependencies**: Managed via `uv` virtual environments (`pyproject.toml` and `uv.lock`). Core dependencies include `fastapi`, `uvicorn`, `openai`, `pillow`, `numpy`, `python-multipart`, and `websockets`.
- **Background Tasks**: `ws_endpoint.py` uses `asyncio.create_task(stream_response())` to execute vision streaming concurrently, allowing immediate cancellation (`active_task.cancel()`) if the client sends a `cancel_stream` message or disconnects.
- **Configuration**: Provider URLs and models can be overridden via environment variables: `LMSTUDIO_BASE_URL`, `LMSTUDIO_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL`.

---

# Frontend Guide

- **Entry Point**: `apps/ui-frontend/index.html` loads Google Fonts (`JetBrains Mono`, `Outfit`) and mounts `/src/main.tsx`, which renders `<App />` (`src/App.tsx`) inside `<React.StrictMode>`.
- **Components**:
  - `App.tsx`: Root component rendering the connection status pill (`.status-pill`), 3D character container (`.pet-container`), and conditional action menu/chat panel (`.chat-panel`).
  - `PetCanvas.tsx` (`src/components/pet/PetCanvas.tsx`): Sets up the Three.js `<Canvas>` with transparent background, WebGPU rendering parameters, ambient/directional lighting, and `<Float>` wrapper around `PetModel`.
  - `PetModel.tsx` (`src/components/pet/PetModel.tsx`): Loads `Soldier.glb` using `useGLTF` and extracts animations (`useAnimations`). Dynamically cross-fades between `Idle`, `Walk` (thinking), and `Run` (talking) actions when `animState` changes, while rotating an orbiting glowing purple torus ring (`#c084fc`) beneath the character.
  - `ChatBubble.tsx` (`src/components/chat/ChatBubble.tsx`): Displays streamed AI responses with auto-scrolling (`scrollTop`), blinking cursor (`.streaming::after`), and a `Stop Streaming` button.
  - `InputBar.tsx` (`src/components/chat/InputBar.tsx`): Controlled text input handling `Enter` key submission and button clicks.
- **Hooks**:
  - `useNativeBridge.ts` (`src/hooks/useNativeBridge.ts`): Detects native `window.chrome.webview` availability. If inside the WPF host, registers event listeners for `message` and posts `JSON.stringify` payloads. If running in a standalone browser tab (`!isNative`), establishes a direct WebSocket connection to `ws://localhost:8000/ws` with exponential backoff and uses `navigator.mediaDevices.getDisplayMedia` + `ImageCapture` / `<video>` canvas fallback to capture browser screenshots locally.
  - `useAIStream.ts` (`src/hooks/useAIStream.ts`): Manages `response` string accumulation via `useRef` to guarantee zero state stuttering during rapid token chunks.
- **State Management**: Local React state (`useState`, `useCallback`, `useRef`) coordinates UI transitions cleanly without external Redux/Zustand libraries.
- **API Communication**: All bidirectional communication routes via JSON string messages over `window.chrome.webview.postMessage` (in C# host) or standard `WebSocket` (in dev browser mode).
- **Build Process**: Powered by Vite and TypeScript (`vite.config.ts`, `tsconfig.json`). `npm run build` runs `tsc` for strict type checking before invoking `vite build` to generate the static SPA bundle inside `/dist`. `.glb` assets are explicitly included via `assetsInclude: ['**/*.glb', '**/*.gltf']`.

---

# Development Commands

### Install All Dependencies
- **Python Backend (`apps/ai-orchestrator`)**:
  ```powershell
  cd apps\ai-orchestrator
  uv venv .venv --python 3.12
  uv pip install -e .
  ```
- **React Frontend (`apps/ui-frontend`)**:
  ```powershell
  cd apps\ui-frontend
  npm install
  ```
- **C# Native Host (`apps/native-host`)**:
  ```powershell
  D:\SyncDevice\dotnet_sdk\dotnet.exe restore apps\native-host\DesktopCompanion.csproj
  ```

### Run All Services Simultaneously (Recommended)
From the repository root, execute the launch batch file to spin up all 3 tiers in separate command windows:
```powershell
.\launch_all.bat
```

### Run Services Individually
- **Run Python AI Orchestrator**:
  ```powershell
  cd apps\ai-orchestrator
  .\.venv\Scripts\python.exe main.py
  # Runs on http://localhost:8000/health and ws://localhost:8000/ws
  ```
- **Run React UI Dev Server**:
  ```powershell
  cd apps\ui-frontend
  npm run dev
  # Runs on http://localhost:3000
  ```
- **Run C# Native Host**:
  ```powershell
  cd apps\native-host
  .\run_host.ps1
  # Or run directly via dotnet:
  D:\SyncDevice\dotnet_sdk\dotnet.exe run --project DesktopCompanion.csproj
  ```

### Run Tests & Verification Checks
- **Python Backend Engine Test**:
  ```powershell
  cd apps\ai-orchestrator
  .\.venv\Scripts\python.exe test_engine.py
  ```
- **Python Syntax & Compilation Check**:
  ```powershell
  cd apps\ai-orchestrator
  .\.venv\Scripts\python.exe -m py_compile main.py test_engine.py api/ws_endpoint.py inference/engine.py inference/prompts.py inference/vision_parser.py
  ```
- **C# Native Host Build Check**:
  ```powershell
  D:\SyncDevice\dotnet_sdk\dotnet.exe build apps\native-host\DesktopCompanion.csproj
  ```

### Build Production Bundle
- **React UI Production SPA Bundle**:
  ```powershell
  cd apps\ui-frontend
  npm run build
  # Outputs production HTML/CSS/JS/GLB assets to apps/ui-frontend/dist/
  ```
- **C# Native Host Release Build**:
  ```powershell
  D:\SyncDevice\dotnet_sdk\dotnet.exe build apps\native-host\DesktopCompanion.csproj -c Release
  ```

---

# AI Agent Instructions

Mandatory rules for future AI coding assistants and developers working on this repository:

1. **Read `PROJECT_MAP.md` First**: Always inspect and understand this architectural intelligence document before modifying code or proposing refactors.
2. **Do Not Rewrite Architecture**: Maintain the exact 3-tier boundary (.NET WPF Host $\leftrightarrow$ React/Vite/R3F UI $\leftrightarrow$ Python/FastAPI Orchestrator). Do not introduce Electron, Tauri, or persistent database layers without explicit user approval.
3. **Preserve Existing Patterns**:
   - **Win32 Hit-Testing**: Do not modify `WM_NCHITTEST` coordinates in `MainWindow.xaml.cs` or `WindowManagement.cs` without rigorous testing across DPI scaling settings.
   - **Binary Frame Protocol**: Keep the WebSocket transport zero-copy binary JPEG (`receive_bytes` / `SendAsync` binary). Do not regress to sending Base64 strings inside JSON payloads over HTTP POST.
   - **Typed IPC**: Use `PostWebMessageAsJson` in C# and `window.chrome.webview.postMessage` in React. Avoid raw string JS injection (`ExecuteScriptAsync`).
4. **Check Existing Implementations Before Adding New Ones**: Check `ScreenCapture.cs`, `useNativeBridge.ts`, and `engine.py` for existing utilities and fallbacks before writing new capture or streaming logic.
5. **Do Not Upgrade Dependencies Without Approval**: Preserve `.NET 9`, `React 19`, `Three.js 0.171+`, and exact pinned versions in `uv.lock` and `package-lock.json` unless explicitly requested by the user.
6. **Run Tests & Builds Before Completing Changes**: After any edit, verify that all three tiers build and check cleanly:
   - Run `D:\SyncDevice\dotnet_sdk\dotnet.exe build apps\native-host\DesktopCompanion.csproj`
   - Run `npm run build` inside `apps\ui-frontend`
   - Run `python -m py_compile ...` inside `apps\ai-orchestrator`
