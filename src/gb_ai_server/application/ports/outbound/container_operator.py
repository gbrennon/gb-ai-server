"""Outbound port - container operator interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from ....domain import CommandResult


class ContainerOperator(ABC):
    """Operate on running containers."""

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
