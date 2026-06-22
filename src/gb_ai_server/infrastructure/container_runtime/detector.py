"""Detect available container runtime."""

from ...application.ports.outbound import ContainerRuntime
from .podman import PodmanRuntime
from .docker import DockerRuntime


class FallbackRuntimeDetector:
    """Detect available container runtime. Prefers Podman, falls back to Docker."""

    @staticmethod
    def detect() -> ContainerRuntime:
        podman = PodmanRuntime()
        if podman.is_available():
            return podman

        docker = DockerRuntime()
        if docker.is_available():
            return docker

        raise RuntimeError(
            "No container runtime found. Install Podman or Docker."
        )
