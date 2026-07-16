"""
mascot_ai/cli/commands/start.py
--------------------------------
`mascot-ai start` — Launch the full Mascot AI Desktop Companion.

What this does (in order):
  1. Check ~/.mascot-ai/.env exists — if not, trigger env setup first.
  2. Start the bundled FastAPI AI Orchestrator on port 8000.
  3. Start a static HTTP server serving the bundled React UI on port 3000.
  4. Download DesktopCompanion.exe from GitHub Releases (first run only,
     cached to ~/.mascot-ai/bin/).
  5. Wait 8 seconds for backend + UI server to come up.
  6. Launch DesktopCompanion.exe — overlay appears on screen.
  7. All output streams into this terminal. Ctrl+C shuts everything down.
"""

import http.server
import importlib.resources
import os
import platform
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

import click
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn

console = Console()

# ── Constants ──────────────────────────────────────────────────────────────
USER_CONFIG_DIR = Path.home() / ".mascot-ai"
ENV_FILE        = USER_CONFIG_DIR / ".env"
BIN_DIR         = USER_CONFIG_DIR / "bin"
HOST_EXE        = BIN_DIR / "DesktopCompanion.exe"

GITHUB_RELEASE_URL = (
    "https://github.com/mohitantil3399/Mascot_ai"
    "/releases/latest/download/DesktopCompanion.exe"
)

STARTUP_DELAY = 8   # seconds — matches launch_all.bat `timeout /t 8`

UI_PORT         = 3000
ORCHESTRATOR_PORT = 8000

os.environ.setdefault("PYTHONIOENCODING", "utf-8")


# ── Helpers ────────────────────────────────────────────────────────────────

def _load_env():
    """Load ~/.mascot-ai/.env into os.environ."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def _prefix_stream(stream, prefix: str, color: str):
    """Read lines from a subprocess stdout and print with a colored prefix."""
    try:
        for raw in iter(stream.readline, b""):
            line = raw.decode("utf-8", errors="replace").rstrip()
            if line:
                console.print(f"[{color}]{prefix}[/{color}] {line}")
    except Exception:
        pass


def _launch_subprocess(label: str, color: str, cmd: list, cwd: Path | None = None, env: dict | None = None) -> subprocess.Popen:
    """Spawn a process, stream its output prefixed with label."""
    rprint(f"[{color}]▶  Starting {label}...[/{color}]")
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    proc_env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        env=proc_env,
    )
    t = threading.Thread(target=_prefix_stream, args=(proc.stdout, label, color), daemon=True)
    t.start()
    return proc


def _start_ui_server() -> threading.Thread:
    """Serve the bundled React UI dist on port 3000 in a background thread."""

    # Locate the ui_dist directory inside the installed package
    try:
        pkg_path = importlib.resources.files("mascot_ai")
        ui_dist_path = Path(str(pkg_path)) / "ui_dist"
    except Exception:
        ui_dist_path = Path(__file__).resolve().parent.parent.parent / "ui_dist"

    if not ui_dist_path.exists():
        rprint(f"[red]✘  Could not find bundled UI at {ui_dist_path}[/red]")
        return None

    class SilentHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ui_dist_path), **kwargs)
        def log_message(self, format, *args):
            pass  # suppress HTTP request logs

    def _serve():
        with http.server.HTTPServer(("localhost", UI_PORT), SilentHandler) as srv:
            srv.serve_forever()

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    rprint(f"[blue]▶  UI server started[/blue] [dim](http://localhost:{UI_PORT})[/dim]")
    return t


def _get_orchestrator_main() -> Path:
    """Return the path to the bundled orchestrator's main.py."""
    try:
        pkg_path = importlib.resources.files("mascot_ai")
        return Path(str(pkg_path)) / "orchestrator" / "main.py"
    except Exception:
        return Path(__file__).resolve().parent.parent.parent / "orchestrator" / "main.py"


def _download_host_exe():
    """Download DesktopCompanion.exe from GitHub Releases if not cached."""
    if HOST_EXE.exists():
        rprint(f"[magenta]▶  Native host found[/magenta] [dim]({HOST_EXE})[/dim]")
        return

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    rprint(f"[magenta]▶  Downloading DesktopCompanion.exe from GitHub Releases...[/magenta]")
    rprint(f"[dim]   {GITHUB_RELEASE_URL}[/dim]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Downloading...", total=None)

            def _report(block_num, block_size, total_size):
                if total_size > 0:
                    progress.update(task, total=total_size,
                                    completed=block_num * block_size)

            urllib.request.urlretrieve(GITHUB_RELEASE_URL, str(HOST_EXE), _report)

        rprint(f"[green]✔[/green]  Downloaded to [dim]{HOST_EXE}[/dim]")

    except Exception as e:
        rprint(f"[red]✘  Download failed: {e}[/red]")
        rprint(
            "\n[yellow]Please download DesktopCompanion.exe manually from:[/yellow]\n"
            f"[link]{GITHUB_RELEASE_URL}[/link]\n"
            f"and place it at: [bold]{HOST_EXE}[/bold]\n"
        )
        raise SystemExit(1)


# ── Command ────────────────────────────────────────────────────────────────

@click.command("start")
def start_cmd():
    """Launch the full Mascot AI Desktop Companion (Ctrl+C to stop)."""

    if platform.system() != "Windows":
        rprint("[red]✘  Mascot AI requires Windows (the native host is a WPF app).[/red]")
        raise SystemExit(1)

    rprint(Panel.fit(
        "[bold cyan]🚀  Mascot AI — Starting Up[/bold cyan]\n"
        "[dim]Press Ctrl+C to stop all services.[/dim]",
        border_style="cyan",
    ))

    # ── Step 1: Check .env ─────────────────────────────────────────────────
    if not ENV_FILE.exists():
        rprint("[yellow]⚠  No config found. Running first-time setup...[/yellow]\n")
        from mascot_ai.cli.commands.env import env_cmd
        from click.testing import CliRunner
        ctx = click.get_current_context()
        ctx.invoke(env_cmd)

    _load_env()

    procs: list[subprocess.Popen] = []

    try:
        # ── Step 2: Start AI Orchestrator ──────────────────────────────────
        orch_main = _get_orchestrator_main()
        procs.append(_launch_subprocess(
            label="[ORCHESTRATOR]",
            color="green",
            cmd=[sys.executable, str(orch_main)],
            cwd=orch_main.parent,
        ))

        # ── Step 3: Serve bundled React UI on port 3000 ────────────────────
        _start_ui_server()

        # ── Step 4: Download native host (cached after first run) ──────────
        _download_host_exe()

        # ── Step 5: 8-second countdown (matches launch_all.bat delay) ──────
        rprint(f"\n[yellow]⏳  Waiting {STARTUP_DELAY}s for services to come up...[/yellow]")
        for remaining in range(STARTUP_DELAY, 0, -1):
            console.print(f"[dim]   {remaining}s...[/dim]", end="\r")
            time.sleep(1)
        console.print()

        # ── Step 6: Launch Native Host (.exe) ─────────────────────────────
        procs.append(_launch_subprocess(
            label="[NATIVE HOST] ",
            color="magenta",
            cmd=[str(HOST_EXE)],
        ))

        # ── Summary ────────────────────────────────────────────────────────
        rprint(Panel.fit(
            "[bold green]✅  Mascot AI is running![/bold green]\n\n"
            "  [green]●[/green]  AI Orchestrator : http://localhost:8000/health\n"
            "  [blue]●[/blue]  UI (built)      : http://localhost:3000\n"
            "  [magenta]●[/magenta]  Desktop overlay : on screen\n\n"
            "[dim]Press [bold]Ctrl+C[/bold] to stop everything.[/dim]",
            border_style="green",
        ))

        for proc in procs:
            proc.wait()

    except KeyboardInterrupt:
        rprint("\n\n[yellow]Shutting down...[/yellow]")
        for proc in procs:
            try:
                proc.terminate()
            except Exception:
                pass
        time.sleep(1)
        for proc in procs:
            try:
                proc.kill()
            except Exception:
                pass
        rprint("[bold red]✘  Stopped.[/bold red]\n")
        sys.exit(0)
