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
    from ...application.ports.outbound import ContainerRuntime, ComposeTool
    from ...application.ports.outbound.model_downloader import ModelDownloader
    from ...application.ports.outbound.model_registrar import ModelRegistrar


class Container:
    """Wires infrastructure implementations to application services."""

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

    def prerequisite_verifier(self) -> PrerequisiteVerifierService:
        return PrerequisiteVerifierService(
            logger=self._logger,
            runtime_detector=self._runtime_detector,
            compose_detector=self._compose_detector,
        )

    def model_downloader(self, downloader: ModelDownloader) -> ModelDownloaderService:
        return ModelDownloaderService(logger=self._logger, downloader=downloader)

    def start_services(self, compose_tool: ComposeTool) -> StartServicesService:
        return StartServicesService(logger=self._logger, compose_tool=compose_tool)

    def stop_services(self, compose_tool: ComposeTool) -> StopServicesService:
        return StopServicesService(logger=self._logger, compose_tool=compose_tool)

    def restart_services(self, compose_tool: ComposeTool) -> RestartServicesService:
        return RestartServicesService(logger=self._logger, compose_tool=compose_tool)

    def list_services(self, compose_tool: ComposeTool) -> ListServicesService:
        return ListServicesService(logger=self._logger, compose_tool=compose_tool)

    def show_logs(self, compose_tool: ComposeTool) -> ShowLogsService:
        return ShowLogsService(logger=self._logger, compose_tool=compose_tool)

    def model_copier(self, runtime: ContainerRuntime) -> ModelCopierService:
        return ModelCopierService(logger=self._logger, container_runtime=runtime)

    def health_verifier(self) -> HealthVerifierService:
        return HealthVerifierService(
            logger=self._logger,
            http_client=self._http_client,
        )

    def model_registrar(self, registrar: ModelRegistrar) -> RegisterModelsService:
        return RegisterModelsService(logger=self._logger, registrar=registrar)
