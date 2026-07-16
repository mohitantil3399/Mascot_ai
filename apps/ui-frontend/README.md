# UI Frontend (React 19 + Three.js)

The user interface tier for Antigravity Desktop Companion. A Vite-powered React SPA featuring a 3D animated mascot character, chat bubbles, and a command input bar — all rendered inside the native host's WebView2 container.

---

## 🔧 Prerequisites

- [Node.js 20+](https://nodejs.org/) (npm is bundled)

---

## 🚀 Setup & Run

```powershell
# Install dependencies
npm install

# Start the dev server
npm run dev
# Dev server starts at http://localhost:3000 (or http://localhost:5173)
```

### Production Build

```powershell
npm run build
npm run preview    # Preview the production build locally
```

---

## 🧩 Key Components

| Component | File | Description |
|-----------|------|-------------|
| **App** | `src/App.tsx` | Root component, layout & state management |
| **PetCanvas** | `src/components/pet/PetCanvas.tsx` | Three.js / R3F canvas for the 3D character |
| **PetModel** | `src/components/pet/PetModel.tsx` | Loads & animates the Soldier.glb model |
| **ChatBubble** | `src/components/chat/ChatBubble.tsx` | AI response chat bubbles |
| **InputBar** | `src/components/chat/InputBar.tsx` | User text input with send functionality |

### Hooks

| Hook | File | Description |
|------|------|-------------|
| **useAIStream** | `src/hooks/useAIStream.ts` | Manages WebSocket AI response streaming |
| **useNativeBridge** | `src/hooks/useNativeBridge.ts` | IPC bridge between React ↔ C# Native Host |

---

## 📁 Structure

```
ui-frontend/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatBubble.tsx      # AI response bubbles
│   │   │   └── InputBar.tsx        # User input bar
│   │   └── pet/
│   │       ├── PetCanvas.tsx       # Three.js canvas container
│   │       ├── PetModel.tsx        # 3D model loader & animator
│   │       └── Soldier.glb         # 3D character asset
│   ├── hooks/
│   │   ├── useAIStream.ts          # AI WebSocket streaming hook
│   │   └── useNativeBridge.ts      # Native host IPC hook
│   ├── types/
│   │   ├── assets.d.ts             # Asset type declarations
│   │   └── ipc.d.ts                # IPC message type declarations
│   ├── App.tsx                     # Root application component
│   ├── index.css                   # Global styles
│   └── main.tsx                    # Vite entry point
├── index.html                      # HTML shell
├── package.json                    # Dependencies & scripts
├── tsconfig.json                   # TypeScript configuration
└── vite.config.ts                  # Vite build configuration
```

---

## 🔗 Dependencies

- **React 19** — UI framework
- **Three.js** — 3D rendering engine
- **@react-three/fiber** — React renderer for Three.js
- **@react-three/drei** — Useful helpers for R3F (loaders, controls, etc.)
- **Vite 6** — Build tool and dev server
- **TypeScript 5.8** — Type safety
