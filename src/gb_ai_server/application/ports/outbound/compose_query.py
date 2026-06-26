"""Outbound port - compose query interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from ....domain import CommandResult


class ComposeQuery(ABC):
    """Compose query operations."""

    @abstractmethod
    def validate(self, compose_file: Path) -> CommandResult:
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
