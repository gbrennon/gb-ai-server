"""Infrastructure layer - adapters for external systems and utilities."""

from .command import Command, CommandResult
from .logging import LogLevel, TerminalLogger
from .config import Environment
from .container_runtime import (
    ContainerInfo,
    PodmanRuntime,
    PodmanInspector,
    PodmanOperator,
    DockerRuntime,
    DockerInspector,
    DockerOperator,
    FallbackRuntimeDetector,
)
from .compose import (
    PodmanComposeStandalone,
    PodmanComposeStandaloneLifecycle,
    PodmanComposeStandaloneQuery,
    PodmanComposeBuiltin,
    PodmanComposeBuiltinLifecycle,
    PodmanComposeBuiltinQuery,
    DockerComposeStandalone,
    DockerComposeStandaloneLifecycle,
    DockerComposeStandaloneQuery,
    DockerComposeBuiltin,
    DockerComposeBuiltinLifecycle,
    DockerComposeBuiltinQuery,
    FallbackComposeDetector,
)
from .persistence import HuggingFaceModelDownloader, ClineModelRegistrar
from .http import CurlHttpClient
from .di import Container, InfrastructureRegistry, VerifierFactory, ComposeServiceFactory, ModelServiceFactory

__all__: list[str] = [
    "Command",
    "CommandResult",
    "LogLevel",
    "TerminalLogger",
    "Environment",
    "ContainerInfo",
    "PodmanRuntime",
    "PodmanInspector",
    "PodmanOperator",
    "DockerRuntime",
    "DockerInspector",
    "DockerOperator",
    "FallbackRuntimeDetector",
    "PodmanComposeStandalone",
    "PodmanComposeStandaloneLifecycle",
    "PodmanComposeStandaloneQuery",
    "PodmanComposeBuiltin",
    "PodmanComposeBuiltinLifecycle",
    "PodmanComposeBuiltinQuery",
    "DockerComposeStandalone",
    "DockerComposeStandaloneLifecycle",
    "DockerComposeStandaloneQuery",
    "DockerComposeBuiltin",
    "DockerComposeBuiltinLifecycle",
    "DockerComposeBuiltinQuery",
    "FallbackComposeDetector",
    "HuggingFaceModelDownloader",
    "CurlHttpClient",
    "ClineModelRegistrar",
    "Container",
    "InfrastructureRegistry",
    "VerifierFactory",
    "ComposeServiceFactory",
    "ModelServiceFactory",
]
