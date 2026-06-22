"""Outbound port - container runtime detector."""

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .container_runtime import ContainerRuntime


class RuntimeDetector(Protocol):
    """Protocol for detecting available container runtime."""

    def detect(self) -> "ContainerRuntime": ...
