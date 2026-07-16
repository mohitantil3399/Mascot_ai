"""
mascot_ai/cli/mascot.py
------------------------
Entry point for the `mascot-ai` CLI command.

Registered via pyproject.toml:
    [project.scripts]
    mascot-ai = "mascot_ai.cli.mascot:cli"
"""

import click
from rich import print as rprint

from mascot_ai.cli.commands.env    import env_cmd
from mascot_ai.cli.commands.start  import start_cmd
from mascot_ai.cli.commands.status import status_cmd


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="1.0.0", prog_name="mascot-ai")
def cli():
    """
    \b
    mascot-ai — Antigravity Desktop Companion

    \b
    Quick start:
      mascot-ai env     ->  set up your API keys (run this first!)
      mascot-ai start   ->  launch the full app
      mascot-ai status  ->  check if services are running

    \b
    The companion runs as a transparent desktop overlay powered by
    a vision AI that watches your screen and responds in real time.
    """
    pass


cli.add_command(env_cmd,    name="env")
cli.add_command(start_cmd,  name="start")
cli.add_command(status_cmd, name="status")


if __name__ == "__main__":
    cli()
