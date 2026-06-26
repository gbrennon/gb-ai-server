"""
llama_bootstrap: Production-ready bootstrap system for llama.cpp.

Hexagonal architecture with strict PEP 695 typing compliance.
Domain logic is pure (100% testable), infrastructure is pluggable.

Layers:
  - Domain: Pure functions, no I/O
  - Application: Orchestration services with inbound/outbound ports
  - Infrastructure: Adapters, CLI, persistence, logging, config
"""

from .infrastructure import (
    Command,
    LogLevel,
    TerminalLogger,
    Environment,
)

from .domain import (
    CommandResult,
    ModelEntry,
    PortAllocator,
    ContainerNamer,
    ResourceRequirements,
    ResourceRequirementsMapper,
    HealthCheckStrategy,
    HealthCheckTimeoutCalculator,
    WaitStrategy,
)

from .application.ports.outbound import (
    ModelDownloader,
    ContainerRuntime,
    ComposeTool,
)

from .infrastructure import (
    ContainerInfo,
    PodmanRuntime,
    PodmanInspector,
    PodmanOperator,
    DockerRuntime,
    DockerInspector,
    DockerOperator,
    FallbackRuntimeDetector,
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
    HuggingFaceModelDownloader,
)

from .application import (
    ModelDownloaderService,
    PrerequisiteVerifierService,
    StartServicesService,
    StopServicesService,
    RestartServicesService,
    ListServicesService,
    ShowLogsService,
    ModelCopierService,
    HealthVerifierService,
)

__version__ = "0.1.0"

__all__: list[str] = [
    # Infrastructure — Command & Config
    "Command",
    "LogLevel",
    "TerminalLogger",
    "Environment",
    # Domain
    "CommandResult",
    "ModelEntry",
    "PortAllocator",
    "ContainerNamer",
    "ResourceRequirements",
    "ResourceRequirementsMapper",
    "HealthCheckStrategy",
    "HealthCheckTimeoutCalculator",
    "WaitStrategy",
    # Outbound Ports
    "ModelDownloader",
    "ContainerRuntime",
    "ComposeTool",
    # Infrastructure — Adapters
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
    # Application
    "ModelDownloaderService",
    "PrerequisiteVerifierService",
    "StartServicesService",
    "StopServicesService",
    "RestartServicesService",
    "ListServicesService",
    "ShowLogsService",
    "ModelCopierService",
    "HealthVerifierService",
]
