"""Compose tool adapters (Docker Compose, Podman Compose)."""

from ..executors.docker import (
    DockerComposeBuiltin,
    DockerComposeBuiltinLifecycle,
    DockerComposeBuiltinQuery,
    DockerComposeStandalone,
    DockerComposeStandaloneLifecycle,
    DockerComposeStandaloneQuery,
)
from ..executors.podman import (
    PodmanComposeBuiltin,
    PodmanComposeBuiltinLifecycle,
    PodmanComposeBuiltinQuery,
    PodmanComposeStandalone,
    PodmanComposeStandaloneLifecycle,
    PodmanComposeStandaloneQuery,
)
from .detector import FallbackComposeDetector

__all__: list[str] = [
    "DockerComposeBuiltin",
    "DockerComposeBuiltinLifecycle",
    "DockerComposeBuiltinQuery",
    "DockerComposeStandalone",
    "DockerComposeStandaloneLifecycle",
    "DockerComposeStandaloneQuery",
    "PodmanComposeBuiltin",
    "PodmanComposeBuiltinLifecycle",
    "PodmanComposeBuiltinQuery",
    "PodmanComposeStandalone",
    "PodmanComposeStandaloneLifecycle",
    "PodmanComposeStandaloneQuery",
    "FallbackComposeDetector",
]
