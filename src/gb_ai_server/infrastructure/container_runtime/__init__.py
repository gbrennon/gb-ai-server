"""Container runtime adapters (Podman, Docker)."""

from .info import ContainerInfo
from .podman import PodmanRuntime
from .docker import DockerRuntime
from .detector import FallbackRuntimeDetector

__all__: list[str] = [
    "ContainerInfo",
    "PodmanRuntime",
    "DockerRuntime",
    "FallbackRuntimeDetector",
]
