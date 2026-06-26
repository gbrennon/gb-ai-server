"""Docker container operator adapter."""

from pathlib import Path

from ...application.ports.outbound import ContainerOperator
from ..command import Command, CommandResult


class DockerOperator(ContainerOperator):
    """Operate on Docker containers."""

    def exec(
        self,
        container_name: str,
        *args: str,
        capture_output: bool = False,
    ) -> CommandResult:
        return Command.run(
            "docker",
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
            "docker",
            "cp",
            str(src),
            f"{container_name}:{dest}",
            capture_output=True,
        )
