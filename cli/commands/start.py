"""
cli/commands/start.py
---------------------
`mascot start` — Start all services in one terminal with live combined output.

Launch order (matches launch_all.bat):
  1. AI Orchestrator  (Python / FastAPI on port 8000)
  2. UI Frontend      (Vite dev server on port 3000)
     ↳ 8-second delay before step 3
  3. Native Host      (C# / WPF dotnet build + run)

All processes write to a single terminal. Press Ctrl+C to stop everything.

  mascot start                  # starts all three tiers
  mascot start orchestrator     # only the Python backend
  mascot start ui               # only the Vite frontend
  mascot start host             # only the .NET WPF host
"""

import os
import signal
import subprocess
import sys
import time
import threading
from pathlib import Path

# Ensure UTF-8 output on all Windows terminals (cp1252 workaround)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import click
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.text import Text

console = Console()

REPO_ROOT    = Path(__file__).resolve().parent.parent.parent
ORCHESTRATOR = REPO_ROOT / "apps" / "ai-orchestrator"
UI_FRONTEND  = REPO_ROOT / "apps" / "ui-frontend"
NATIVE_HOST  = REPO_ROOT / "apps" / "native-host"

# Delay (seconds) between UI/orchestrator start and native host start
# (matches the `timeout /t 8` in launch_all.bat)
STARTUP_DELAY_SECONDS = 8

TIERS = ["orchestrator", "ui", "host"]


def _prefix_stream(stream, prefix: str, color: str):
    """Read lines from a subprocess stream, printing each with a colored prefix."""
    try:
        for raw in iter(stream.readline, b""):
            line = raw.decode("utf-8", errors="replace").rstrip()
            console.print(f"[{color}]{prefix}[/{color}]  {line}")
    except Exception:
        pass


def _launch(label: str, color: str, cmd: list[str], cwd: Path) -> subprocess.Popen:
    """Spawn a subprocess and pipe its stdout+stderr into the current terminal."""
    rprint(f"\n[{color}]▶  Starting {label}[/{color}]")
    rprint(f"[dim]   cwd: {cwd}[/dim]")
    rprint(f"[dim]   cmd: {' '.join(cmd)}[/dim]\n")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        env=env,
    )

    thread = threading.Thread(
        target=_prefix_stream,
        args=(proc.stdout, label, color),
        daemon=True,
    )
    thread.start()

    return proc


def _build_orchestrator_cmd() -> list[str]:
    """Return the correct python executable path inside the venv."""
    venv_python = ORCHESTRATOR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        python = str(venv_python)
    else:
        python = sys.executable  # fallback to current env python
    return [python, "main.py"]


def _build_host_cmd() -> list[str]:
    """Return dotnet run command for the native host."""
    return ["dotnet", "run", "--project", "DesktopCompanion.csproj"]


@click.command("start")
@click.argument("tier", required=False, type=click.Choice(TIERS, case_sensitive=False))
def start_cmd(tier: str | None):
    """Start services in one terminal (Ctrl+C to stop all).

    \b
    TIER (optional):
      orchestrator  — Python FastAPI server  (port 8000)
      ui            — Vite dev server        (port 3000)
      host          — C# WPF native overlay
    
    When no TIER is given, all three start in sequence with an 8-second
    delay before the native host (matching the original launch_all.bat).
    """

    rprint(Panel.fit(
        "[bold cyan]🚀  Mascot AI — Starting Services[/bold cyan]\n"
        "[dim]Press [bold]Ctrl+C[/bold] to stop everything.[/dim]",
        border_style="cyan",
    ))

    procs: list[subprocess.Popen] = []

    try:
        # ── Tier 1: AI Orchestrator ──────────────────────────────────────
        if tier is None or tier == "orchestrator":
            procs.append(_launch(
                label="[ORCHESTRATOR]",
                color="green",
                cmd=_build_orchestrator_cmd(),
                cwd=ORCHESTRATOR,
            ))

        # ── Tier 2: UI Frontend ──────────────────────────────────────────
        if tier is None or tier == "ui":
            procs.append(_launch(
                label="[UI FRONTEND] ",
                color="blue",
                cmd=["npm", "run", "dev"],
                cwd=UI_FRONTEND,
            ))

        # ── Delay before Native Host (only when starting all) ────────────
        if tier is None:
            rprint(
                f"\n[yellow]⏳  Waiting {STARTUP_DELAY_SECONDS}s for backend & dev server "
                f"to come up before starting Native Host…[/yellow]"
            )
            for remaining in range(STARTUP_DELAY_SECONDS, 0, -1):
                console.print(
                    f"[dim]   {remaining}s remaining…[/dim]",
                    end="\r",
                )
                time.sleep(1)
            console.print()  # newline after countdown

        # ── Tier 3: Native Host ──────────────────────────────────────────
        if tier is None or tier == "host":
            procs.append(_launch(
                label="[NATIVE HOST]  ",
                color="magenta",
                cmd=_build_host_cmd(),
                cwd=NATIVE_HOST,
            ))

        rprint(Panel.fit(
            "[bold green]✅  All services started![/bold green]\n\n"
            "  [green]●[/green]  AI Orchestrator : [link=http://localhost:8000/health]http://localhost:8000/health[/link]\n"
            "  [blue]●[/blue]  UI Frontend     : [link=http://localhost:3000]http://localhost:3000[/link]\n"
            "  [magenta]●[/magenta]  Native Host     : desktop overlay window\n\n"
            "[dim]Press [bold]Ctrl+C[/bold] to stop all services.[/dim]",
            border_style="green",
        ))

        # Wait for all processes to finish (or Ctrl+C)
        for proc in procs:
            proc.wait()

    except KeyboardInterrupt:
        rprint("\n\n[yellow]⚠  Ctrl+C detected — shutting down all services…[/yellow]")
        for proc in procs:
            try:
                proc.terminate()
            except Exception:
                pass
        # Give them a moment to clean up
        time.sleep(1)
        for proc in procs:
            try:
                proc.kill()
            except Exception:
                pass
        rprint("[bold red]✘  All services stopped.[/bold red]\n")
        sys.exit(0)
