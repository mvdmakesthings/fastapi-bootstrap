"""
Main CLI entry point for the FastAPI Bootstrap CLI.
"""

import click

from cli.commands.deploy import deploy_cmd
from cli.commands.dev import dev_cmd
from cli.commands.infra import infra_cmd

# Import command groups
from cli.commands.init import init_cmd


@click.group()
@click.version_option()
def cli():
    """FastAPI Bootstrap CLI - Manage your FastAPI application."""
    pass


# Register commands
cli.add_command(init_cmd)
cli.add_command(dev_cmd)
cli.add_command(infra_cmd)
cli.add_command(deploy_cmd)

if __name__ == "__main__":
    cli()
