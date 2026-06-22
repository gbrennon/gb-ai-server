"""Infrastructure layer - adapters for external systems and utilities."""

from .command import Command, CommandResult
from .logging import LogLevel, TerminalLogger
from .config import Environment
from .container_runtime import (
    ContainerInfo,
    PodmanRuntime,
    DockerRuntime,
    FallbackRuntimeDetector,
)
from .compose import (
    PodmanComposeStandalone,
    PodmanComposeBuiltin,
    DockerComposeStandalone,
    DockerComposeBuiltin,
    FallbackComposeDetector,
)
from .persistence import HuggingFaceModelDownloader
from .http import CurlHttpClient
from .di import Container

__all__: list[str] = [
    "Command",
    "CommandResult",
    "LogLevel",
    "TerminalLogger",
    "Environment",
    "ContainerInfo",
    "PodmanRuntime",
    "DockerRuntime",
    "FallbackRuntimeDetector",
    "PodmanComposeStandalone",
    "PodmanComposeBuiltin",
    "DockerComposeStandalone",
    "DockerComposeBuiltin",
    "FallbackComposeDetector",
    "HuggingFaceModelDownloader",
    "CurlHttpClient",
    "Container",
]
