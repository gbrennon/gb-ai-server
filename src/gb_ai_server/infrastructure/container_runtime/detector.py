"""Detect available container runtime."""

from ...application.ports.outbound.runtime_detector import RuntimeDetection
from .podman_runtime import PodmanRuntime
from .podman_inspector import PodmanInspector
from .podman_operator import PodmanOperator
from .docker_runtime import DockerRuntime
from .docker_inspector import DockerInspector
from .docker_operator import DockerOperator


class FallbackRuntimeDetector:
    """Detect available container runtime. Prefers Podman, falls back to Docker."""

    @staticmethod
    def detect() -> RuntimeDetection:
        podman_runtime = PodmanRuntime()
        if podman_runtime.is_available():
            return RuntimeDetection(
                runtime=podman_runtime,
                inspector=PodmanInspector(),
                operator=PodmanOperator(),
            )

        docker_runtime = DockerRuntime()
        if docker_runtime.is_available():
            return RuntimeDetection(
                runtime=docker_runtime,
                inspector=DockerInspector(),
                operator=DockerOperator(),
            )

        raise RuntimeError(
            "No container runtime found. Install Podman or Docker."
        )
