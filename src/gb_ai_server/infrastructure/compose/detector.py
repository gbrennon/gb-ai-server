"""Detect available compose tool with fallback strategy."""

from dataclasses import dataclass
from ...application.ports.outbound import ComposeTool, ComposeLifecycle, ComposeQuery
from ...application.ports.outbound.compose_detection import ComposeDetection
from ..podman import (
    PodmanComposeStandalone,
    PodmanComposeStandaloneLifecycle,
    PodmanComposeStandaloneQuery,
    PodmanComposeBuiltin,
    PodmanComposeBuiltinLifecycle,
    PodmanComposeBuiltinQuery,
)
from ..docker import (
    DockerComposeStandalone,
    DockerComposeStandaloneLifecycle,
    DockerComposeStandaloneQuery,
    DockerComposeBuiltin,
    DockerComposeBuiltinLifecycle,
    DockerComposeBuiltinQuery,
)


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
