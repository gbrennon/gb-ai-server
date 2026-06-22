"""docker compose (built-in) tool."""

from pathlib import Path

from ...application.ports.outbound import ComposeTool
from ..command import Command, CommandResult


class DockerComposeBuiltin(ComposeTool):
    """docker compose (built-in) tool."""

    @property
    def name(self) -> str:
        return "docker-compose-builtin"

    @property
    def pretty_name(self) -> str:
        return "docker compose (built-in)"

    def is_available(self) -> bool:
        result = Command.run(
            "docker",
            "compose",
            "version",
            capture_output=True,
        )
        return result.success

    def validate(self, compose_file: Path) -> CommandResult:
        return Command.run(
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "config",
            capture_output=True,
        )

    def up(
        self,
        compose_file: Path,
        *services: str,
        detach: bool = True,
    ) -> CommandResult:
        args = [
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "up",
        ]
        if detach:
            args.append("-d")
        args.extend(services)
        return Command.run(*args, capture_output=True)

    def down(self, compose_file: Path) -> CommandResult:
        return Command.run(
            "docker",
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
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "restart",
        ]
        args.extend(services)
        return Command.run(*args, capture_output=True)

    def ps(self, compose_file: Path) -> CommandResult:
        return Command.run(
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "ps",
            capture_output=True,
        )

    def logs(
        self,
        compose_file: Path,
        service: str | None = None,
        follow: bool = False,
    ) -> CommandResult:
        args = [
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "logs",
        ]
        if follow:
            args.append("-f")
        if service:
            args.append(service)
        return Command.run(*args, capture_output=True)
