"""Outbound port - compose tool interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from ....domain import CommandResult


class ComposeTool(ABC):
    """Abstract compose tool interface."""

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def validate(self, compose_file: Path) -> CommandResult:
        pass

    @abstractmethod
    def up(
        self,
        compose_file: Path,
        *services: str,
        detach: bool = True,
    ) -> CommandResult:
        pass

    @abstractmethod
    def down(self, compose_file: Path) -> CommandResult:
        pass

    @abstractmethod
    def restart(
        self,
        compose_file: Path,
        *services: str,
    ) -> CommandResult:
        pass

    @abstractmethod
    def ps(self, compose_file: Path) -> CommandResult:
        pass

    @abstractmethod
    def logs(
        self,
        compose_file: Path,
        service: str | None = None,
        follow: bool = False,
    ) -> CommandResult:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def pretty_name(self) -> str:
        pass
