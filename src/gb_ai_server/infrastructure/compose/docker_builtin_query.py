"""Docker built-in compose query operations."""

from pathlib import Path

from ...application.ports.outbound import ComposeQuery
from ..command import Command, CommandResult


class DockerComposeBuiltinQuery(ComposeQuery):
    """Docker built-in compose query operations."""

    def validate(self, compose_file: Path) -> CommandResult:
        return Command.run(
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "config",
            capture_output=True,
        )

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
