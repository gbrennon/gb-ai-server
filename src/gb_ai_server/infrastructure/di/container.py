"""Dependency injection container wiring infrastructure to application services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...application.services import (
    ModelDownloaderService,
    PrerequisiteVerifierService,
    StartServicesService,
    StopServicesService,
    RestartServicesService,
    ListServicesService,
    ShowLogsService,
    ModelCopierService,
    HealthVerifierService,
    RegisterModelsService,
)
from ..logging import TerminalLogger
from ..container_runtime.detector import FallbackRuntimeDetector
from ..compose.detector import FallbackComposeDetector
from ..http.curl_client import CurlHttpClient

if TYPE_CHECKING:
    from ...application.ports.outbound import ContainerInspector, ContainerOperator, ComposeLifecycle, ComposeQuery
    from ...application.ports.outbound.model_downloader import ModelDownloader
    from ...application.ports.outbound.model_registrar import ModelRegistrar


class InfrastructureRegistry:
    """Registry for core infrastructure components (properties only)."""

    def __init__(self) -> None:
        self._logger = TerminalLogger()
        self._runtime_detector = FallbackRuntimeDetector()
        self._compose_detector = FallbackComposeDetector()
        self._http_client = CurlHttpClient()

    @property
    def logger(self) -> TerminalLogger:
        return self._logger

    @property
    def runtime_detector(self) -> FallbackRuntimeDetector:
        return self._runtime_detector

    @property
    def compose_detector(self) -> FallbackComposeDetector:
        return self._compose_detector

    @property
    def http_client(self) -> CurlHttpClient:
        return self._http_client


class VerifierFactory:
    """Factory for system and health verifier services."""

    def __init__(self, registry: InfrastructureRegistry) -> None:
        self._registry = registry

    def prerequisite_verifier(self) -> PrerequisiteVerifierService:
        return PrerequisiteVerifierService(
            logger=self._registry.logger,
            runtime_detector=self._registry.runtime_detector,
            compose_detector=self._registry.compose_detector,
        )

    def health_verifier(self) -> HealthVerifierService:
        return HealthVerifierService(
            logger=self._registry.logger,
            http_client=self._registry.http_client,
        )


class ComposeServiceFactory:
    """Factory for compose tool operations and services."""

    def __init__(self, registry: InfrastructureRegistry) -> None:
        self._registry = registry

    def start_services(self, lifecycle: ComposeLifecycle) -> StartServicesService:
        return StartServicesService(logger=self._registry.logger, compose_lifecycle=lifecycle)

    def stop_services(self, lifecycle: ComposeLifecycle) -> StopServicesService:
        return StopServicesService(logger=self._registry.logger, compose_lifecycle=lifecycle)

    def restart_services(self, lifecycle: ComposeLifecycle) -> RestartServicesService:
        return RestartServicesService(logger=self._registry.logger, compose_lifecycle=lifecycle)

    def list_services(self, query: ComposeQuery) -> ListServicesService:
        return ListServicesService(logger=self._registry.logger, compose_query=query)

    def show_logs(self, query: ComposeQuery) -> ShowLogsService:
        return ShowLogsService(logger=self._registry.logger, compose_query=query)


class ModelServiceFactory:
    """Factory for downloading, copying, and registering model services."""

    def __init__(self, registry: InfrastructureRegistry) -> None:
        self._registry = registry

    def model_downloader(self, downloader: ModelDownloader) -> ModelDownloaderService:
        return ModelDownloaderService(logger=self._registry.logger, downloader=downloader)

    def model_copier(
        self,
        inspector: ContainerInspector,
        operator: ContainerOperator,
    ) -> ModelCopierService:
        return ModelCopierService(
            logger=self._registry.logger,
            inspector=inspector,
            operator=operator,
        )

    def model_registrar(self, registrar: ModelRegistrar) -> RegisterModelsService:
        return RegisterModelsService(logger=self._registry.logger, registrar=registrar)


class Container:
    """Wires infrastructure implementations to application services.

    Acts as a facade over the decomposed factories to maintain backward compatibility.
    """

    def __init__(self) -> None:
        self.infrastructure = InfrastructureRegistry()
        self.verifiers = VerifierFactory(self.infrastructure)
        self.compose = ComposeServiceFactory(self.infrastructure)
        self.models = ModelServiceFactory(self.infrastructure)

    @property
    def logger(self) -> TerminalLogger:
        return self.infrastructure.logger

    @property
    def runtime_detector(self) -> FallbackRuntimeDetector:
        return self.infrastructure.runtime_detector

    @property
    def compose_detector(self) -> FallbackComposeDetector:
        return self.infrastructure.compose_detector

    @property
    def http_client(self) -> CurlHttpClient:
        return self.infrastructure.http_client

    def prerequisite_verifier(self) -> PrerequisiteVerifierService:
        return self.verifiers.prerequisite_verifier()

    def model_downloader(self, downloader: ModelDownloader) -> ModelDownloaderService:
        return self.models.model_downloader(downloader)

    def start_services(self, lifecycle: ComposeLifecycle) -> StartServicesService:
        return self.compose.start_services(lifecycle)

    def stop_services(self, lifecycle: ComposeLifecycle) -> StopServicesService:
        return self.compose.stop_services(lifecycle)

    def restart_services(self, lifecycle: ComposeLifecycle) -> RestartServicesService:
        return self.compose.restart_services(lifecycle)

    def list_services(self, query: ComposeQuery) -> ListServicesService:
        return self.compose.list_services(query)

    def show_logs(self, query: ComposeQuery) -> ShowLogsService:
        return self.compose.show_logs(query)

    def model_copier(
        self,
        inspector: ContainerInspector,
        operator: ContainerOperator,
    ) -> ModelCopierService:
        return self.models.model_copier(inspector, operator)

    def health_verifier(self) -> HealthVerifierService:
        return self.verifiers.health_verifier()

    def model_registrar(self, registrar: ModelRegistrar) -> RegisterModelsService:
        return self.models.model_registrar(registrar)
