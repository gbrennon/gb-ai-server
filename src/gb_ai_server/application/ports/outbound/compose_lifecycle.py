"""Outbound port - compose lifecycle interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from ....domain import CommandResult


class ComposeLifecycle(ABC):
    """Compose lifecycle operations."""

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
    def restart(self, compose_file: Path, *services: str) -> CommandResult:
        pass
