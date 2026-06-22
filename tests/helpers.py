"""Shared test helpers for infrastructure fixture scripts."""

from pathlib import Path


def make_script(bin_dir: Path, name: str, stdout: str = "", stderr: str = "", exit_code: int = 0) -> Path:
    """Create an executable shell script in *bin_dir*.

    The script writes *stdout* to stdout, *stderr* to stderr, then exits with *exit_code*.
    """
    path = bin_dir / name
    parts: list[str] = []
    if stdout:
        parts.append(f"echo '{stdout}'")
    if stderr:
        parts.append(f"echo '{stderr}' >&2")
    body = "\n".join(parts) if parts else ""
    script = f"#!/bin/sh\n{body}\nexit {exit_code}\n"
    path.write_text(script)
    path.chmod(0o755)
    return path


def install_podman(bin_dir: Path) -> None:
    """Install fixture scripts that simulate podman."""
    make_script(bin_dir, "podman", stdout="CONTAINER ID  IMAGE", exit_code=0)


def install_podman_compose(bin_dir: Path) -> None:
    """Install fixture scripts for podman-compose standalone."""
    install_podman(bin_dir)
    make_script(bin_dir, "podman-compose", stdout="compose ok", exit_code=0)


def install_docker(bin_dir: Path) -> None:
    """Install fixture scripts that simulate docker."""
    make_script(bin_dir, "docker", stdout="CONTAINER ID  IMAGE", exit_code=0)


def install_docker_compose(bin_dir: Path) -> None:
    """Install fixture scripts for docker-compose standalone."""
    install_docker(bin_dir)
    make_script(bin_dir, "docker-compose", stdout="compose ok", exit_code=0)
