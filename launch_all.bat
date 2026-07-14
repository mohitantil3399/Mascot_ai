@echo off
REM launch_all.bat — starts all three tiers of the Desktop Companion.
REM Place this file at the repo root (next to /apps) and just double-click it,
REM or run it from a terminal. Each tier opens in its own window so you can
REM see its logs; closing a window stops that tier.

setlocal
set ROOT=%~dp0
set DOTNET_EXE=D:\SyncDevice\dotnet_sdk\dotnet.exe

echo Starting AI Orchestrator (Python / FastAPI)...
start "AI Orchestrator" cmd /k "cd /d "%ROOT%apps\ai-orchestrator" && if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat && python main.py) else (if exist .venv\Scripts\python.exe (.venv\Scripts\python.exe main.py) else (echo No .venv found - please run: uv venv .venv ^&^& uv pip install -e .))"

echo Starting UI (React / Vite)...
start "UI Frontend" cmd /k "cd /d "%ROOT%apps\ui-frontend" && (if not exist node_modules (echo Installing npm dependencies... && call npm install)) && npm run dev"

echo Waiting a few seconds for the backend/dev server to come up...
timeout /t 8 /nobreak >nul

echo Starting Native Host (C# / WPF)...
start "Native Host" powershell -NoExit -ExecutionPolicy Bypass -Command "& '%DOTNET_EXE%' build '%ROOT%apps\native-host\DesktopCompanion.csproj'; & '%ROOT%apps\native-host\run_host.ps1'"

echo.
echo All three tiers launching in separate windows:
echo   - AI Orchestrator : http://localhost:8000/health  (ws://localhost:8000/ws)
echo   - UI Frontend     : http://localhost:3000
echo   - Native Host     : the desktop overlay window
echo.
echo Close this window any time - it is not needed once the others are running.
pause
endlocal
