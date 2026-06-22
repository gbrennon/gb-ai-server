"""Detect available compose tool with fallback strategy."""

from ...application.ports.outbound import ComposeTool
from .podman_standalone import PodmanComposeStandalone
from .podman_builtin import PodmanComposeBuiltin
from .docker_standalone import DockerComposeStandalone
from .docker_builtin import DockerComposeBuiltin


class FallbackComposeDetector:
    """Detect available compose tool with fallback strategy."""

    STRATEGIES: list[type[ComposeTool]] = [
        PodmanComposeStandalone,
        PodmanComposeBuiltin,
        DockerComposeStandalone,
        DockerComposeBuiltin,
    ]

    @staticmethod
    def detect() -> ComposeTool:
        for strategy_class in FallbackComposeDetector.STRATEGIES:
            tool = strategy_class()
            if tool.is_available():
                return tool

        raise RuntimeError(
            "No compose tool found. Install docker-compose or podman-compose."
        )
