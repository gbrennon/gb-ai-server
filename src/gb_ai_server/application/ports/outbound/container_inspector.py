"""Outbound port - container inspector interface."""

from abc import ABC, abstractmethod

from ....domain import CommandResult


class ContainerInspector(ABC):
    """Inspect running containers."""

    @abstractmethod
    def is_running(self, container_name: str) -> bool:
        pass

    @abstractmethod
    def get_env(self, container_name: str, var_name: str) -> str | None:
        pass

    @abstractmethod
    def ps(self) -> CommandResult:
        pass

    @abstractmethod
    def logs(self, container_name: str, follow: bool = False) -> CommandResult:
        pass
