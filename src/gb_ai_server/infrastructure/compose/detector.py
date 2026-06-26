"""Detect available compose tool with fallback strategy."""

from dataclasses import dataclass
from ...application.ports.outbound import ComposeTool, ComposeLifecycle, ComposeQuery
from ...application.ports.outbound.compose_detection import ComposeDetection
from .podman_standalone_runtime import PodmanComposeStandalone
from .podman_standalone_lifecycle import PodmanComposeStandaloneLifecycle
from .podman_standalone_query import PodmanComposeStandaloneQuery
from .podman_builtin_runtime import PodmanComposeBuiltin
from .podman_builtin_lifecycle import PodmanComposeBuiltinLifecycle
from .podman_builtin_query import PodmanComposeBuiltinQuery
from .docker_standalone_runtime import DockerComposeStandalone
from .docker_standalone_lifecycle import DockerComposeStandaloneLifecycle
from .docker_standalone_query import DockerComposeStandaloneQuery
from .docker_builtin_runtime import DockerComposeBuiltin
from .docker_builtin_lifecycle import DockerComposeBuiltinLifecycle
from .docker_builtin_query import DockerComposeBuiltinQuery


@dataclass
class _Strategy:
    tool: type[ComposeTool]
    lifecycle: type[ComposeLifecycle]
    query: type[ComposeQuery]


class FallbackComposeDetector:
    """Detect available compose tool with fallback strategy."""

    STRATEGIES: list[_Strategy] = [
        _Strategy(
            PodmanComposeStandalone, PodmanComposeStandaloneLifecycle, PodmanComposeStandaloneQuery
        ),
        _Strategy(
            PodmanComposeBuiltin, PodmanComposeBuiltinLifecycle, PodmanComposeBuiltinQuery
        ),
        _Strategy(
            DockerComposeStandalone, DockerComposeStandaloneLifecycle, DockerComposeStandaloneQuery
        ),
        _Strategy(
            DockerComposeBuiltin, DockerComposeBuiltinLifecycle, DockerComposeBuiltinQuery
        ),
    ]

    @staticmethod
    def detect() -> ComposeDetection:
        for strategy in FallbackComposeDetector.STRATEGIES:
            tool = strategy.tool()
            if tool.is_available():
                return ComposeDetection(
                    tool=tool,
                    lifecycle=strategy.lifecycle(),
                    query=strategy.query(),
                )

        raise RuntimeError(
            "No compose tool found. Install docker-compose or podman-compose."
        )
