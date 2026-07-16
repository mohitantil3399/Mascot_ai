"""
cli/commands/install.py
-----------------------
`mascot install` — Install dependencies for all (or specific) tiers.

  mascot install            # installs all three tiers
  mascot install ui         # only npm install for the frontend
  mascot install orchestrator  # only uv pip install for the Python backend
  mascot install host       # only dotnet restore for the C# native host
"""

import subprocess
import sys
from pathlib import Path

import click
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

console = Console()

REPO_ROOT    = Path(__file__).resolve().parent.parent.parent
ORCHESTRATOR = REPO_ROOT / "apps" / "ai-orchestrator"
UI_FRONTEND  = REPO_ROOT / "apps" / "ui-frontend"
NATIVE_HOST  = REPO_ROOT / "apps" / "native-host"

TIERS = ["orchestrator", "ui", "host"]


def _run(label: str, cmd: list[str], cwd: Path):
    """Run a shell command, streaming output to the terminal."""
    rprint(f"\n[bold cyan]▶  {label}[/bold cyan]")
    rprint(f"[dim]   {' '.join(cmd)}[/dim]\n")

    result = subprocess.run(cmd, cwd=str(cwd))
    if result.returncode != 0:
        rprint(f"[bold red]✘[/bold red]  [red]{label} failed (exit {result.returncode})[/red]")
        raise SystemExit(result.returncode)

    rprint(f"[bold green]✔[/bold green]  {label} done.\n")


def _install_orchestrator():
    _run(
        "AI Orchestrator — uv pip install",
        ["uv", "pip", "install", "-e", "."],
        ORCHESTRATOR,
    )


def _install_ui():
    _run(
        "UI Frontend — npm install",
        ["npm", "install"],
        UI_FRONTEND,
    )


def _install_host():
    _run(
        "Native Host — dotnet restore",
        ["dotnet", "restore", "DesktopCompanion.csproj"],
        NATIVE_HOST,
    )


@click.command("install")
@click.argument("tier", required=False, type=click.Choice(TIERS, case_sensitive=False))
def install_cmd(tier: str | None):
    """Install dependencies for all tiers (or a specific one).

    \b
    TIER (optional):
      orchestrator  — Python / uv pip install
      ui            — Node.js / npm install
      host          — C# / dotnet restore
    """

    rprint(Panel.fit(
        "[bold cyan]📦  Mascot AI — Install Dependencies[/bold cyan]",
        border_style="cyan",
    ))

    if tier is None or tier == "orchestrator":
        _install_orchestrator()
    if tier is None or tier == "ui":
        _install_ui()
    if tier is None or tier == "host":
        _install_host()

    rprint(Panel.fit(
        "[bold green]✅  All dependencies installed![/bold green]\n\n"
        "Next step: run [bold cyan]mascot start[/bold cyan]",
        border_style="green",
    ))
