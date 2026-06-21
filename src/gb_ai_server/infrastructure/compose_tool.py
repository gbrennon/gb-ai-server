"""Compose tool adapters."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..core import Command, CommandResult


class ComposeTool(ABC):
    """Abstract compose tool interface."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if compose tool is available."""
        pass

    @abstractmethod
    def validate(self, compose_file: Path) -> CommandResult:
        """Validate compose file."""
        pass

    @abstractmethod
    def up(
        self,
        compose_file: Path,
        *services: str,
        detach: bool = True,
    ) -> CommandResult:
        """Start services."""
        pass

    @abstractmethod
    def down(self, compose_file: Path) -> CommandResult:
        """Stop services."""
        pass

    @abstractmethod
    def restart(
        self,
        compose_file: Path,
        *services: str,
    ) -> CommandResult:
        """Restart services."""
        pass

    @abstractmethod
    def ps(self, compose_file: Path) -> CommandResult:
        """List services."""
        pass

    @abstractmethod
    def logs(
        self,
        compose_file: Path,
        service: str | None = None,
        follow: bool = False,
    ) -> CommandResult:
        """Get service logs."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Compose tool name."""
        pass

    @property
    @abstractmethod
    def pretty_name(self) -> str:
        """Human-readable compose tool name."""
        pass


class PodmanComposeStandalone(ComposeTool):
    """podman-compose standalone tool."""

    @property
    def name(self) -> str:
        return "podman-compose"

    @property
    def pretty_name(self) -> str:
        return "podman-compose (standalone)"

    def is_available(self) -> bool:
        """Check if podman-compose is available."""
        return Command.exists("podman-compose")

    def validate(self, compose_file: Path) -> CommandResult:
        """Validate compose file."""
        return Command.run(
            "podman-compose",
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
        """Start services."""
        args = [
            "podman-compose",
            "-f",
            str(compose_file),
            "up",
        ]
        if detach:
            args.append("-d")
        args.extend(services)
        return Command.run(*args, capture_output=True)

    def down(self, compose_file: Path) -> CommandResult:
        """Stop services."""
        return Command.run(
            "podman-compose",
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
        """Restart services."""
        args = [
            "podman-compose",
            "-f",
            str(compose_file),
            "restart",
        ]
        args.extend(services)
        return Command.run(*args, capture_output=True)

    def ps(self, compose_file: Path) -> CommandResult:
        """List services."""
        return Command.run(
            "podman-compose",
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
        """Get service logs."""
        args = [
            "podman-compose",
            "-f",
            str(compose_file),
            "logs",
        ]
        if follow:
            args.append("-f")
        if service:
            args.append(service)
        return Command.run(*args, capture_output=True)


class PodmanComposeBuiltin(ComposeTool):
    """podman compose (built-in) tool."""

    @property
    def name(self) -> str:
        return "podman-compose-builtin"

    @property
    def pretty_name(self) -> str:
        return "podman compose (built-in)"

    def is_available(self) -> bool:
        """Check if podman compose is available."""
        result = Command.run(
            "podman",
            "compose",
            "version",
            capture_output=True,
        )
        return result.success

    def validate(self, compose_file: Path) -> CommandResult:
        """Validate compose file."""
        return Command.run(
            "podman",
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
        """Start services."""
        args = [
            "podman",
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
        """Stop services."""
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
        """Restart services."""
        args = [
            "podman",
            "compose",
            "-f",
            str(compose_file),
            "restart",
        ]
        args.extend(services)
        return Command.run(*args, capture_output=True)

    def ps(self, compose_file: Path) -> CommandResult:
        """List services."""
        return Command.run(
            "podman",
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
        """Get service logs."""
        args = [
            "podman",
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


class DockerComposeStandalone(ComposeTool):
    """docker-compose standalone tool."""

    @property
    def name(self) -> str:
        return "docker-compose"

    @property
    def pretty_name(self) -> str:
        return "docker-compose (standalone)"

    def is_available(self) -> bool:
        """Check if docker-compose is available."""
        return Command.exists("docker-compose")

    def validate(self, compose_file: Path) -> CommandResult:
        """Validate compose file."""
        return Command.run(
            "docker-compose",
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
        """Start services."""
        args = [
            "docker-compose",
            "-f",
            str(compose_file),
            "up",
        ]
        if detach:
            args.append("-d")
        args.extend(services)
        return Command.run(*args, capture_output=True)

    def down(self, compose_file: Path) -> CommandResult:
        """Stop services."""
        return Command.run(
            "docker-compose",
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
        """Restart services."""
        args = [
            "docker-compose",
            "-f",
            str(compose_file),
            "restart",
        ]
        args.extend(services)
        return Command.run(*args, capture_output=True)

    def ps(self, compose_file: Path) -> CommandResult:
        """List services."""
        return Command.run(
            "docker-compose",
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
        """Get service logs."""
        args = [
            "docker-compose",
            "-f",
            str(compose_file),
            "logs",
        ]
        if follow:
            args.append("-f")
        if service:
            args.append(service)
        return Command.run(*args, capture_output=True)


class DockerComposeBuiltin(ComposeTool):
    """docker compose (built-in) tool."""

    @property
    def name(self) -> str:
        return "docker-compose-builtin"

    @property
    def pretty_name(self) -> str:
        return "docker compose (built-in)"

    def is_available(self) -> bool:
        """Check if docker compose is available."""
        result = Command.run(
            "docker",
            "compose",
            "version",
            capture_output=True,
        )
        return result.success

    def validate(self, compose_file: Path) -> CommandResult:
        """Validate compose file."""
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
        """Start services."""
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
        """Stop services."""
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
        """Restart services."""
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
        """List services."""
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
        """Get service logs."""
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


class ComposeToolDetector:
    """Detect available compose tool with fallback strategy."""

    # Priority order for compose tools
    STRATEGIES: list[type[ComposeTool]] = [
        PodmanComposeStandalone,
        PodmanComposeBuiltin,
        DockerComposeStandalone,
        DockerComposeBuiltin,
    ]

    @staticmethod
    def detect() -> ComposeTool:
        """
        Detect available compose tool.

        Tries strategies in priority order.

        Returns:
            ComposeTool instance.

        Raises:
            RuntimeError: If no compose tool available.
        """
        for strategy_class in ComposeToolDetector.STRATEGIES:
            tool = strategy_class()
            if tool.is_available():
                return tool

        raise RuntimeError(
            "No compose tool found. Install docker-compose or podman-compose."
        )
