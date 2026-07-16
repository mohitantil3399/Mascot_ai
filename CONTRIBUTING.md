# Contributing to Antigravity Desktop Companion

Thank you for your interest in contributing! This guide will help you get set up and understand our workflow.

---

## 🛠️ Development Setup

### Prerequisites

Make sure you have the following installed:

- [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0) (for the Native Host)
- [Python 3.12+](https://www.python.org/downloads/) (for the AI Orchestrator)
- [uv](https://docs.astral.sh/uv/) — Python environment and package manager
- [Node.js 20+](https://nodejs.org/) (for the UI Frontend)

### Fork & Clone

```bash
# Fork the repo on GitHub, then clone your fork:
git clone https://github.com/<your-username>/Mascot_ai.git
cd Mascot_ai
```

### Setup Each Tier

**AI Orchestrator:**
```powershell
cd apps/ai-orchestrator
cp .env.example .env          # Edit .env with your API key(s)
uv venv .venv --python 3.12
uv pip install -e .
.venv\Scripts\python.exe main.py
```

**UI Frontend:**
```powershell
cd apps/ui-frontend
npm install
npm run dev
```

**Native Host:**
```powershell
cd apps/native-host
cp run_host.ps1.example run_host.ps1    # Edit paths if needed
dotnet build
.\run_host.ps1
```

---

## 📝 Code Style

- **Python**: Follow PEP 8. Use type hints where practical.
- **TypeScript/React**: Use the existing TSConfig settings. Prefer functional components with hooks.
- **C#**: Follow .NET conventions. Use nullable reference types (enabled in the `.csproj`).

---

## 🔀 Git Workflow

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit with clear, descriptive messages:
   ```bash
   git commit -m "Add: brief description of what was added"
   git commit -m "Fix: brief description of what was fixed"
   ```

3. **Push your branch** and open a Pull Request:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **PR Guidelines:**
   - Keep PRs focused on a single change or feature
   - Include a clear description of what changed and why
   - Reference any related issues (e.g., `Closes #12`)
   - Ensure the project builds and runs correctly

---

## 📂 Project Structure

| Directory | Language | Purpose |
|-----------|----------|---------|
| `apps/ai-orchestrator/` | Python | FastAPI backend, vision LLM engine |
| `apps/native-host/` | C# | WPF desktop overlay, screen capture |
| `apps/ui-frontend/` | TypeScript | React + Three.js chat UI |
| `libs/shared-types/` | TypeScript | Shared WebSocket & IPC protocol types |

---

## ⚙️ Machine-Specific Files

The following files are **gitignored** because they contain machine-specific paths:

| File | Template |
|------|----------|
| `launch_all.bat` | `launch_all.bat.example` |
| `apps/native-host/run_host.ps1` | `run_host.ps1.example` |
| `apps/native-host/sign_build.ps1` | `sign_build.ps1.example` |
| `apps/ai-orchestrator/.env` | `.env.example` |

Copy each `.example` file, remove the `.example` suffix, and customize for your environment.

---

## 🐛 Reporting Issues

- Use [GitHub Issues](https://github.com/mohitantil3399/Mascot_ai/issues) to report bugs or request features
- Include your OS version, .NET SDK version, Python version, and Node.js version
- Provide steps to reproduce the issue

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the [GPL-3.0 License](LICENSE).
