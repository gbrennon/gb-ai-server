"""Podman built-in compose lifecycle."""

from pathlib import Path

from ...application.ports.outbound import ComposeLifecycle
from ..command import Command, CommandResult


class PodmanComposeBuiltinLifecycle(ComposeLifecycle):
    """Podman built-in compose lifecycle operations."""

    def up(
        self,
        compose_file: Path,
        *services: str,
        detach: bool = True,
    ) -> CommandResult:
        args = [
            "podman",
            "compose",
            "-f",
            str(compose_file),
            "up",
        ]
        if detach:
            args.append("-d")
        args.append("--force-recreate")
        args.extend(services)
        return Command.run(*args, capture_output=True)

    def down(self, compose_file: Path) -> CommandResult:
        return Command.run(
            "podman",
            "compose",
            "-f",
            str(compose_file),
            "down",
            "--timeout",
            "0",
            capture_output=True,
        )

    def restart(
        self,
        compose_file: Path,
        *services: str,
    ) -> CommandResult:
        args = [
            "podman",
            "compose",
            "-f",
            str(compose_file),
            "restart",
        ]
        args.extend(services)
        return Command.run(*args, capture_output=True)
