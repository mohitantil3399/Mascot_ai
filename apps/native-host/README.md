# Native Host (C# / WPF Desktop Overlay)

The Windows desktop overlay tier for Antigravity Desktop Companion. Creates a transparent, always-on-top WPF window with DWM Glass effects, GPU-accelerated screen capture, and a WebView2 container for the React UI.

---

## 🔧 Prerequisites

- [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0) (version 9.0.314+)
- **Windows 10** (build 19041 or later) or **Windows 11**
- [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (usually pre-installed on Windows 10/11)

---

## 🚀 Setup & Run

### 1. Copy the Example Scripts

```powershell
cp run_host.ps1.example run_host.ps1
cp sign_build.ps1.example sign_build.ps1
# Edit the scripts if you have a custom .NET SDK path
```

### 2. Build & Run

```powershell
# Option A: Use the run script
.\run_host.ps1

# Option B: Manual build and run
dotnet build
dotnet run
```

### 3. Code Signing (Optional)

```powershell
# Sign build output with a self-signed cert (for dev) or your own cert:
.\sign_build.ps1
```

---

## 🏗️ Architecture

The native host provides three key capabilities:

### DWM Glass Window
- Transparent, click-through overlay using `DwmExtendFrameIntoClientArea`
- `WS_EX_TOOLWINDOW | WS_EX_TOPMOST` styles for always-on-top, taskbar-hidden behavior
- Dynamic hit-testing via `WM_NCHITTEST` — routes clicks between the UI and background apps

### Screen Capture Pipeline
- **ScreenCapture.cs** — GPU-accelerated desktop capture
- **ActiveWindowTracker.cs** — Tracks the active window for Region of Interest (ROI) capture
- Captures are downscaled to max 1024px and encoded as JPEG

### WebView2 Bridge
- Hosts the React UI inside a `WebView2` control
- IPC via `PostWebMessageAsJson` / `WebMessageReceived`
- Forwards AI responses from the WebSocket client to the React UI

---

## 📁 Structure

```
native-host/
├── NativeInterop/
│   ├── ActiveWindowTracker.cs   # Win32 foreground window tracking
│   ├── ScreenCapture.cs         # GPU-accelerated screen capture
│   └── WindowManagement.cs      # DWM Glass, hit-testing, window styles
├── Services/
│   ├── AIWebSocketClient.cs     # WebSocket client to AI Orchestrator
│   └── WebViewBridge.cs         # WebView2 ↔ C# IPC bridge
├── App.xaml / App.xaml.cs       # WPF application entry point
├── MainWindow.xaml / .cs        # Main overlay window
├── DesktopCompanion.csproj      # Project file (net9.0-windows10.0.19041.0)
├── global.json                  # .NET SDK version pinning
├── run_host.ps1.example         # Build & run template
└── sign_build.ps1.example       # Code-signing template
```

---

## ⚠️ Notes

- This tier is **Windows-only** due to its use of WPF, Win32 APIs, and DWM.
- The `global.json` pins the .NET SDK to `9.0.x` with `rollForward: latestPatch`.
- If you have a non-standard .NET SDK installation, edit `run_host.ps1` to point to your `dotnet.exe`.
