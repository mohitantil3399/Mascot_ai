"""
cli/mascot.py
-------------
Main entry point for the `mascot` CLI tool.

Registered as a console script in pyproject.toml:
    [project.scripts]
    mascot = "cli.mascot:cli"

After `uv pip install -e .` from the repo root, run `mascot --help`.
"""

import click
from rich import print as rprint
from rich.panel import Panel

from cli.commands.env     import env_cmd
from cli.commands.install import install_cmd
from cli.commands.start   import start_cmd
from cli.commands.build   import build_cmd
from cli.commands.status  import status_cmd

BANNER = """\
[bold cyan]
  __  __                     _        _    ___
 |  \\/  |__ _ ___ __ ___  _| |_     / \\  |_ _|
 | |\\/| / _` (_-</ _/ _ \\|_   _|   / _ \\  | |
 |_|  |_\\__,_/__/\\__\\___/  |_|    /_/ \\_\\|___|
[/bold cyan]
[dim]  Antigravity Desktop Companion — Developer CLI  v1.0[/dim]
"""


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version="1.0.0", prog_name="mascot")
def cli():
    """
    \b
    mascot — developer CLI for the Mascot AI project.

    \b
    Common workflow:
      mascot env        ->  configure API keys (run first!)
      mascot install    ->  install all dependencies
      mascot start      ->  launch all services
      mascot status     ->  check if services are running
      mascot build      ->  build production artifacts

    Run [mascot COMMAND --help] for details on any command.
    """
    pass


# ── Register all sub-commands ────────────────────────────────────────────────
cli.add_command(env_cmd,     name="env")
cli.add_command(install_cmd, name="install")
cli.add_command(start_cmd,   name="start")
cli.add_command(build_cmd,   name="build")
cli.add_command(status_cmd,  name="status")


if __name__ == "__main__":
    cli()
