"""Detect available container runtime."""

from ...application.ports.outbound.runtime_detector import RuntimeDetection
from ..podman import PodmanRuntime, PodmanInspector, PodmanOperator
from ..docker import DockerRuntime, DockerInspector, DockerOperator


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
