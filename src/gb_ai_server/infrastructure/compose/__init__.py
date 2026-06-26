"""Compose tool adapters (Docker Compose, Podman Compose)."""

from .docker_builtin_runtime import DockerComposeBuiltin
from .docker_builtin_lifecycle import DockerComposeBuiltinLifecycle
from .docker_builtin_query import DockerComposeBuiltinQuery
from .docker_standalone_runtime import DockerComposeStandalone
from .docker_standalone_lifecycle import DockerComposeStandaloneLifecycle
from .docker_standalone_query import DockerComposeStandaloneQuery
from .podman_builtin_runtime import PodmanComposeBuiltin
from .podman_builtin_lifecycle import PodmanComposeBuiltinLifecycle
from .podman_builtin_query import PodmanComposeBuiltinQuery
from .podman_standalone_runtime import PodmanComposeStandalone
from .podman_standalone_lifecycle import PodmanComposeStandaloneLifecycle
from .podman_standalone_query import PodmanComposeStandaloneQuery
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
