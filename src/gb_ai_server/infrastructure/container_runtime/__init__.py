"""Container runtime adapters (Podman, Docker)."""

from .info import ContainerInfo
from .podman_runtime import PodmanRuntime
from .podman_inspector import PodmanInspector
from .podman_operator import PodmanOperator
from .docker_runtime import DockerRuntime
from .docker_inspector import DockerInspector
from .docker_operator import DockerOperator
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
