"""Podman container operator adapter."""

from pathlib import Path

from ....application.ports.outbound import ContainerOperator
from ...command import Command, CommandResult


class PodmanOperator(ContainerOperator):
    """Operate on Podman containers."""

    def exec(
        self,
        container_name: str,
        *args: str,
        capture_output: bool = False,
    ) -> CommandResult:
        return Command.run(
            "podman",
            "exec",
            container_name,
            *args,
            capture_output=capture_output,
        )

    def copy_to(
        self,
        src: Path | str,
        container_name: str,
        dest: Path | str,
    ) -> CommandResult:
        return Command.run(
            "podman",
            "cp",
            str(src),
            f"{container_name}:{dest}",
            capture_output=True,
        )
