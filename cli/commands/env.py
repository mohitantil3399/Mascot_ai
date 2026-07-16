"""
cli/commands/env.py
-------------------
`mascot env` — Interactive first-time environment setup.

Copies `.env.example` → `.env` in the ai-orchestrator directory,
then prompts the user for their API keys and writes them in.
"""

import os
import re
import shutil
from pathlib import Path

import click
from rich import print as rprint
from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import Console

console = Console()

# Root of the repo (two levels up from cli/commands/)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_EXAMPLE = REPO_ROOT / "apps" / "ai-orchestrator" / ".env.example"
ENV_FILE    = REPO_ROOT / "apps" / "ai-orchestrator" / ".env"


# Keys we actively prompt for (in order of importance)
PROMPT_KEYS = [
    {
        "key": "MISTRAL_API_KEY",
        "label": "Mistral API Key",
        "url": "https://console.mistral.ai",
        "required": True,
        "placeholder": "your_mistral_api_key_here",
    },
    {
        "key": "OPENROUTER_API_KEY",
        "label": "OpenRouter API Key (optional fallback)",
        "url": "https://openrouter.ai/keys",
        "required": False,
        "placeholder": "your_openrouter_api_key_here",
    },
    {
        "key": "OPENAI_API_KEY",
        "label": "OpenAI API Key (optional fallback)",
        "url": "https://platform.openai.com/api-keys",
        "required": False,
        "placeholder": "your_openai_api_key_here",
    },
]


def _write_key_to_env(env_path: Path, key: str, value: str):
    """Replace a placeholder value (or commented-out line) in the .env file."""
    content = env_path.read_text(encoding="utf-8")

    # Try to replace an existing uncommented assignment
    pattern_uncommented = re.compile(rf"^({re.escape(key)}=).*$", re.MULTILINE)
    # Try to un-comment and replace a commented-out assignment
    pattern_commented = re.compile(rf"^#\s*({re.escape(key)}=).*$", re.MULTILINE)

    if pattern_uncommented.search(content):
        content = pattern_uncommented.sub(rf"\g<1>{value}", content)
    elif pattern_commented.search(content):
        # Uncomment the line and set the value
        content = pattern_commented.sub(rf"{key}={value}", content)
    else:
        # Append at the end
        content += f"\n{key}={value}\n"

    env_path.write_text(content, encoding="utf-8")


@click.command("env")
@click.option(
    "--force", "-f",
    is_flag=True,
    default=False,
    help="Re-run setup even if .env already exists.",
)
def env_cmd(force: bool):
    """Set up the .env file and configure API keys interactively."""

    rprint(Panel.fit(
        "[bold cyan]🔑  Mascot AI — Environment Setup[/bold cyan]\n"
        "[dim]This will guide you through configuring your API keys.[/dim]",
        border_style="cyan",
    ))

    # Check if .env already exists
    if ENV_FILE.exists() and not force:
        rprint(f"\n[green]✔[/green]  [bold].env[/bold] already exists at "
               f"[dim]{ENV_FILE}[/dim]")
        rprint("[dim]Run [bold]mascot env --force[/bold] to reconfigure.[/dim]\n")
        return

    if not ENV_EXAMPLE.exists():
        rprint(f"[red]✘[/red]  Could not find [bold].env.example[/bold] at "
               f"[dim]{ENV_EXAMPLE}[/dim]")
        raise click.Abort()

    # Copy the example file
    shutil.copy(ENV_EXAMPLE, ENV_FILE)
    rprint(f"\n[green]✔[/green]  Copied [bold].env.example[/bold] → [bold].env[/bold]\n")

    # Interactively ask for each key
    rprint("[bold white]Please enter your API keys below.[/bold white]")
    rprint("[dim]Press Enter to skip optional keys. You can always edit "
           "[bold].env[/bold] manually later.[/dim]\n")

    for item in PROMPT_KEYS:
        required_tag = "[bold red](required)[/bold red]" if item["required"] else "[dim](optional)[/dim]"
        rprint(f"  [bold yellow]{item['label']}[/bold yellow] {required_tag}")
        rprint(f"  [dim]Get yours at: {item['url']}[/dim]")

        while True:
            value = Prompt.ask(
                f"  [cyan]{item['key']}[/cyan]",
                default="" if not item["required"] else None,
                password=True,   # hides input like a password field
                console=console,
            )

            # Skip optional keys
            if not value and not item["required"]:
                rprint(f"  [dim]↳ Skipped (optional)[/dim]\n")
                break

            # Enforce required keys
            if not value and item["required"]:
                rprint(f"  [red]This key is required. Please enter a value.[/red]")
                continue

            _write_key_to_env(ENV_FILE, item["key"], value)
            rprint(f"  [green]✔[/green] Saved.\n")
            break

    rprint(Panel.fit(
        "[bold green]✅  Environment configured![/bold green]\n\n"
        f"Your keys are stored in [bold]{ENV_FILE}[/bold]\n"
        "[dim]This file is gitignored — your keys are safe.[/dim]\n\n"
        "Next step: run [bold cyan]mascot install[/bold cyan]",
        border_style="green",
    ))
