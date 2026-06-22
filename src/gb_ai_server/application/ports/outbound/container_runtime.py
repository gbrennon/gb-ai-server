"""Outbound port - container runtime interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from ....domain import CommandResult


class ContainerRuntime(ABC):
    """Abstract container runtime interface."""

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def is_running(self, container_name: str) -> bool:
        pass

    @abstractmethod
    def exec(
        self,
        container_name: str,
        *args: str,
        capture_output: bool = False,
    ) -> CommandResult:
        pass

    @abstractmethod
    def copy_to(
        self,
        src: Path | str,
        container_name: str,
        dest: Path | str,
    ) -> CommandResult:
        pass

    @abstractmethod
    def ps(self) -> CommandResult:
        pass

    @abstractmethod
    def logs(self, container_name: str, follow: bool = False) -> CommandResult:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def pretty_name(self) -> str:
        pass
