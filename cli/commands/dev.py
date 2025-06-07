"""
Development environment commands.
"""

import subprocess
from pathlib import Path

import click


@click.group(name="dev")
def dev_cmd():
    """Manage local development environment."""
    pass


@dev_cmd.command(name="start")
@click.option("--detached", is_flag=True, help="Run in detached mode")
def start_dev_environment(detached):
    """Start the local development environment."""
    click.echo("Starting local development environment...")

    project_root = Path(__file__).resolve().parents[4]
    docker_compose_file = (
        project_root / "infrastructure" / "docker" / "docker-compose.dev.yml"
    )

    if not docker_compose_file.exists():
        click.echo(
            f"Error: Docker Compose file not found at {docker_compose_file}", err=True
        )
        return

    # Build the docker-compose command
    cmd = ["docker-compose", "-f", str(docker_compose_file)]

    if detached:
        cmd.extend(["up", "-d"])
    else:
        cmd.append("up")

    click.echo(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error starting development environment: {e}", err=True)
        return

    click.echo("Development environment started successfully!")


@dev_cmd.command(name="stop")
def stop_dev_environment():
    """Stop the local development environment."""
    click.echo("Stopping local development environment...")

    project_root = Path(__file__).resolve().parents[4]
    docker_compose_file = (
        project_root / "infrastructure" / "docker" / "docker-compose.dev.yml"
    )

    if not docker_compose_file.exists():
        click.echo(
            f"Error: Docker Compose file not found at {docker_compose_file}", err=True
        )
        return

    cmd = ["docker-compose", "-f", str(docker_compose_file), "down"]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error stopping development environment: {e}", err=True)
        return

    click.echo("Development environment stopped successfully!")
