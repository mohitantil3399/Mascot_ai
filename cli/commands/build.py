"""
cli/commands/build.py
---------------------
`mascot build` — Build production artifacts for tiers that support it.

  mascot build           # builds UI (npm run build) + dotnet host
  mascot build ui        # only npm run build
  mascot build host      # only dotnet publish

Note: The AI Orchestrator has no build step (pure Python).
"""

import subprocess
from pathlib import Path

import click
from rich import print as rprint
from rich.panel import Panel

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
UI_FRONTEND = REPO_ROOT / "apps" / "ui-frontend"
NATIVE_HOST = REPO_ROOT / "apps" / "native-host"

TIERS = ["ui", "host"]


def _run(label: str, cmd: list[str], cwd: Path):
    rprint(f"\n[bold cyan]▶  {label}[/bold cyan]")
    rprint(f"[dim]   {' '.join(cmd)}[/dim]\n")
    result = subprocess.run(cmd, cwd=str(cwd))
    if result.returncode != 0:
        rprint(f"[bold red]✘[/bold red]  {label} failed (exit {result.returncode})")
        raise SystemExit(result.returncode)
    rprint(f"[bold green]✔[/bold green]  {label} done.\n")


@click.command("build")
@click.argument("tier", required=False, type=click.Choice(TIERS, case_sensitive=False))
def build_cmd(tier: str | None):
    """Build production artifacts for UI and/or Native Host.

    \b
    TIER (optional):
      ui    — npm run build  (output in apps/ui-frontend/dist/)
      host  — dotnet publish (Release build)
    """

    rprint(Panel.fit(
        "[bold cyan]🔨  Mascot AI — Build[/bold cyan]",
        border_style="cyan",
    ))

    if tier is None or tier == "ui":
        _run(
            "UI Frontend — npm run build",
            ["npm", "run", "build"],
            UI_FRONTEND,
        )

    if tier is None or tier == "host":
        _run(
            "Native Host — dotnet publish (Release)",
            ["dotnet", "publish", "DesktopCompanion.csproj",
             "-c", "Release", "--self-contained", "false"],
            NATIVE_HOST,
        )

    rprint(Panel.fit(
        "[bold green]✅  Build complete![/bold green]",
        border_style="green",
    ))
