"""
cli/commands/status.py
----------------------
`mascot status` — Check whether each service is running by probing its port.

  mascot status   # checks orchestrator (8000) and UI (3000)
"""

import socket
import urllib.request
import urllib.error
from pathlib import Path

import click
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

console = Console()


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Return True if a TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _http_get(url: str, timeout: float = 2.0) -> tuple[bool, str]:
    """Return (success, body_or_error)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return True, resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return False, str(e)


@click.command("status")
def status_cmd():
    """Check whether each Mascot AI service is currently running."""

    rprint(Panel.fit(
        "[bold cyan]📡  Mascot AI — Service Status[/bold cyan]",
        border_style="cyan",
    ))

    table = Table(show_header=True, header_style="bold white", box=None, padding=(0, 2))
    table.add_column("Service",       style="bold")
    table.add_column("Port",          justify="center")
    table.add_column("Status",        justify="center")
    table.add_column("Health",        justify="left")

    # ── AI Orchestrator ──────────────────────────────────────────────────
    orch_up   = _port_open("localhost", 8000)
    orch_icon = "[bold green]● RUNNING[/bold green]" if orch_up else "[bold red]○ STOPPED[/bold red]"

    health_detail = ""
    if orch_up:
        ok, body = _http_get("http://localhost:8000/health")
        health_detail = f"[dim]{body[:60]}[/dim]" if ok else f"[yellow]{body[:60]}[/yellow]"

    table.add_row("AI Orchestrator", "8000", orch_icon, health_detail)

    # ── UI Frontend ──────────────────────────────────────────────────────
    ui_up   = _port_open("localhost", 3000)
    ui_icon = "[bold green]● RUNNING[/bold green]" if ui_up else "[bold red]○ STOPPED[/bold red]"
    table.add_row("UI Frontend", "3000", ui_icon, "")

    # ── Native Host (no fixed port — check by process name heuristic) ───
    # We don't have a port to probe, so just note it.
    table.add_row(
        "Native Host (WPF)", "—",
        "[dim]Cannot probe[/dim]",
        "[dim]Check for the overlay window[/dim]",
    )

    console.print(table)
    rprint()

    if orch_up and ui_up:
        rprint("[bold green]✅  Core services are running.[/bold green]")
    else:
        rprint("[bold yellow]⚠  Some services are not running. "
               "Run [cyan]mascot start[/cyan] to launch them.[/bold yellow]")
