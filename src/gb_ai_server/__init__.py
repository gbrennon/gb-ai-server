"""
llama_bootstrap: Production-ready bootstrap system for llama.cpp.

Hexagonal architecture with strict PEP 695 typing compliance.
Domain logic is pure (100% testable), infrastructure is pluggable.

Layers:
  - Domain: Pure functions, no I/O (llama_bootstrap.domain)
  - Application: Orchestration services (llama_bootstrap.application)
  - Infrastructure: Adapters for Docker/Podman (llama_bootstrap.infrastructure)
  - Core: Shared utilities (llama_bootstrap.core)
"""

from .core import (
    Logger,
    LogLevel,
    Environment,
    Command,
    CommandResult,
)

from .domain import (
    ModelEntry,
    PortAllocator,
    ContainerNamer,
    ResourceRequirements,
    ResourceRequirementsMapper,
    HealthCheckStrategy,
    HealthCheckTimeoutCalculator,
    WaitStrategy,
    ModelDownloader,
)

from .infrastructure import (
    ContainerRuntime,
    ContainerInfo,
    PodmanRuntime,
    DockerRuntime,
    RuntimeDetector,
    ComposeTool,
    PodmanComposeStandalone,
    PodmanComposeBuiltin,
    DockerComposeStandalone,
    DockerComposeBuiltin,
    ComposeToolDetector,
    HuggingFaceModelDownloader,
)

from .application import (
    ModelDownloadService,
    PrerequisiteVerifier,
    ServiceOrchestrator,
    ModelCopier,
    HealthVerifier,
)

__version__ = "0.1.0"

__all__: list[str] = [
    # Core
    "Logger",
    "LogLevel",
    "Environment",
    "Command",
    "CommandResult",
    # Domain
    "ModelEntry",
    "PortAllocator",
    "ContainerNamer",
    "ResourceRequirements",
    "ResourceRequirementsMapper",
    "HealthCheckStrategy",
    "HealthCheckTimeoutCalculator",
    "WaitStrategy",
    "ModelDownloader",
    # Infrastructure
    "ContainerRuntime",
    "ContainerInfo",
    "PodmanRuntime",
    "DockerRuntime",
    "RuntimeDetector",
    "ComposeTool",
    "PodmanComposeStandalone",
    "PodmanComposeBuiltin",
    "DockerComposeStandalone",
    "DockerComposeBuiltin",
    "ComposeToolDetector",
    "HuggingFaceModelDownloader",
    # Application
    "ModelDownloadService",
    "PrerequisiteVerifier",
    "ServiceOrchestrator",
    "ModelCopier",
    "HealthVerifier",
]
