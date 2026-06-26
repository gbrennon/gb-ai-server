"""Outbound port - container runtime detector and detection result."""

from dataclasses import dataclass
from typing import Protocol

from .container_runtime import ContainerRuntime
from .container_inspector import ContainerInspector
from .container_operator import ContainerOperator


@dataclass
class RuntimeDetection:
    """Result of container runtime detection."""

    runtime: ContainerRuntime
    inspector: ContainerInspector
    operator: ContainerOperator


class RuntimeDetector(Protocol):
    """Protocol for detecting available container runtime."""

    def detect(self) -> RuntimeDetection: ...
