"""Container runtime adapters for Podman and Docker."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ..core import Command, CommandResult


@dataclass
class ContainerInfo:
    """Information about a running container."""

    name: str
    image: str
    status: str
    ports: dict[int, int]


class ContainerRuntime(ABC):
    """Abstract container runtime interface."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if runtime is available."""
        pass

    @abstractmethod
    def is_running(self, container_name: str) -> bool:
        """Check if container is running."""
        pass

    @abstractmethod
    def exec(
        self,
        container_name: str,
        *args: str,
        capture_output: bool = False,
    ) -> CommandResult:
        """Execute command in container."""
        pass

    @abstractmethod
    def copy_to(
        self,
        src: Path | str,
        container_name: str,
        dest: Path | str,
    ) -> CommandResult:
        """Copy file to container."""
        pass

    @abstractmethod
    def ps(self) -> CommandResult:
        """List containers."""
        pass

    @abstractmethod
    def logs(self, container_name: str, follow: bool = False) -> CommandResult:
        """Get container logs."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Runtime name (e.g., 'podman', 'docker')."""
        pass

    @property
    @abstractmethod
    def pretty_name(self) -> str:
        """Human-readable runtime name."""
        pass


class PodmanRuntime(ContainerRuntime):
    """Podman container runtime adapter."""

    @property
    def name(self) -> str:
        return "podman"

    @property
    def pretty_name(self) -> str:
        return "Podman"

    def is_available(self) -> bool:
        """Check if Podman is available and responsive."""
        if not Command.exists("podman"):
            return False
        result = Command.run("podman", "ps", capture_output=True)
        return result.success

    def is_running(self, container_name: str) -> bool:
        """Check if Podman container is running."""
        result = Command.run(
            "podman",
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
        """Execute command in Podman container."""
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
        """Copy file to Podman container."""
        return Command.run(
            "podman",
            "cp",
            str(src),
            f"{container_name}:{dest}",
            capture_output=True,
        )

    def ps(self) -> CommandResult:
        """List Podman containers."""
        return Command.run("podman", "ps", capture_output=True)

    def logs(self, container_name: str, follow: bool = False) -> CommandResult:
        """Get Podman container logs."""
        args = ["podman", "logs"]
        if follow:
            args.append("-f")
        args.append(container_name)
        return Command.run(*args, capture_output=True)


class DockerRuntime(ContainerRuntime):
    """Docker container runtime adapter."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def pretty_name(self) -> str:
        return "Docker"

    def is_available(self) -> bool:
        """Check if Docker is available and responsive."""
        if not Command.exists("docker"):
            return False
        result = Command.run("docker", "ps", capture_output=True)
        return result.success

    def is_running(self, container_name: str) -> bool:
        """Check if Docker container is running."""
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
        """Execute command in Docker container."""
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
        """Copy file to Docker container."""
        return Command.run(
            "docker",
            "cp",
            str(src),
            f"{container_name}:{dest}",
            capture_output=True,
        )

    def ps(self) -> CommandResult:
        """List Docker containers."""
        return Command.run("docker", "ps", capture_output=True)

    def logs(self, container_name: str, follow: bool = False) -> CommandResult:
        """Get Docker container logs."""
        args = ["docker", "logs"]
        if follow:
            args.append("-f")
        args.append(container_name)
        return Command.run(*args, capture_output=True)


class RuntimeDetector:
    """Detect available container runtime."""

    @staticmethod
    def detect() -> ContainerRuntime:
        """
        Detect available container runtime.

        Prefers Podman, falls back to Docker.

        Returns:
            ContainerRuntime instance.

        Raises:
            RuntimeError: If no runtime available.
        """
        podman = PodmanRuntime()
        if podman.is_available():
            return podman

        docker = DockerRuntime()
        if docker.is_available():
            return docker

        raise RuntimeError(
            "No container runtime found. Install Podman or Docker."
        )
