"""Docker container runtime adapter."""

from pathlib import Path

from ...application.ports.outbound import ContainerRuntime
from ..command import Command, CommandResult


class DockerRuntime(ContainerRuntime):
    """Docker container runtime adapter."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def pretty_name(self) -> str:
        return "Docker"

    def is_available(self) -> bool:
        if not Command.exists("docker"):
            return False
        result = Command.run("docker", "ps", capture_output=True)
        return result.success

    def is_running(self, container_name: str) -> bool:
        result = Command.run(
            "docker",
            "inspect",
            "-f",
            "{{.State.Running}}",
            container_name,
            capture_output=True,
        )
        return result.success and result.stdout.strip() == "true"

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

    def ps(self) -> CommandResult:
        return Command.run("docker", "ps", capture_output=True)

    def logs(self, container_name: str, follow: bool = False) -> CommandResult:
        args = ["docker", "logs"]
        if follow:
            args.append("-f")
        args.append(container_name)
        return Command.run(*args, capture_output=True)
