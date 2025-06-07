"""
Docker utilities for the FastAPI Bootstrap CLI.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional


def build_image(
    dockerfile_path: Path,
    tag: str,
    context_path: Optional[Path] = None,
    build_args: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Build a Docker image.

    Args:
        dockerfile_path: Path to the Dockerfile
        tag: Image tag
        context_path: Build context path (defaults to Dockerfile directory)
        build_args: Build arguments

    Returns:
        bool: True if build was successful, False otherwise
    """
    if not dockerfile_path.exists():
        print(f"Error: Dockerfile not found at {dockerfile_path}")
        return False

    if context_path is None:
        context_path = dockerfile_path.parent

    cmd = ["docker", "build", "-f", str(dockerfile_path), "-t", tag]

    if build_args:
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])

    cmd.append(str(context_path))

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building Docker image: {e}")
        return False


def push_image(tag: str) -> bool:
    """
    Push a Docker image to a registry.

    Args:
        tag: Image tag

    Returns:
        bool: True if push was successful, False otherwise
    """
    cmd = ["docker", "push", tag]

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error pushing Docker image: {e}")
        return False


def docker_compose_up(
    compose_file: Path, detached: bool = False, services: Optional[List[str]] = None
) -> bool:
    """
    Run docker-compose up.

    Args:
        compose_file: Path to the docker-compose file
        detached: Run in detached mode
        services: Specific services to start

    Returns:
        bool: True if command was successful, False otherwise
    """
    if not compose_file.exists():
        print(f"Error: Docker Compose file not found at {compose_file}")
        return False

    cmd = ["docker-compose", "-f", str(compose_file)]

    if detached:
        cmd.extend(["up", "-d"])
    else:
        cmd.append("up")

    if services:
        cmd.extend(services)

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running docker-compose: {e}")
        return False


def docker_compose_down(compose_file: Path, remove_volumes: bool = False) -> bool:
    """
    Run docker-compose down.

    Args:
        compose_file: Path to the docker-compose file
        remove_volumes: Remove volumes when stopping containers

    Returns:
        bool: True if command was successful, False otherwise
    """
    if not compose_file.exists():
        print(f"Error: Docker Compose file not found at {compose_file}")
        return False

    cmd = ["docker-compose", "-f", str(compose_file), "down"]

    if remove_volumes:
        cmd.append("-v")

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running docker-compose down: {e}")
        return False


def is_docker_running() -> bool:
    """
    Check if Docker daemon is running.

    Returns:
        bool: True if Docker is running, False otherwise
    """
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
