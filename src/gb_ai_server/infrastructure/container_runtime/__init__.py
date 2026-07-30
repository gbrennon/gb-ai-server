"""Container runtime adapters (Podman, Docker)."""

from .info import ContainerInfo
from ..executors.podman import PodmanRuntime, PodmanInspector, PodmanOperator
from ..executors.docker import DockerRuntime, DockerInspector, DockerOperator
from .detector import FallbackRuntimeDetector

__all__: list[str] = [
    "ContainerInfo",
    "PodmanRuntime",
    "PodmanInspector",
    "PodmanOperator",
    "DockerRuntime",
    "DockerInspector",
    "DockerOperator",
    "FallbackRuntimeDetector",
]
