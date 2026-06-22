"""Console output formatting for the bootstrap CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gb_ai_server.application.ports.outbound import Logger


class BootstrapPresenter:
    """Formats bootstrap workflow output for the console."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def no_models_configured(self) -> None:
        self._logger.error("No models configured")

    def prerequisites_failed(self) -> None:
        self._logger.error("Prerequisites not met")

    def detection_failed(self) -> None:
        self._logger.error("Failed to detect compose tool or runtime")

    def skipping_download(self) -> None:
        self._logger.info("Skipping model download (--skip-download)")

    def all_downloads_failed(self) -> None:
        self._logger.warn("All model downloads failed")

    def start_services_failed(self) -> None:
        self._logger.error("Failed to start services")

    def copy_models_failed(self) -> None:
        self._logger.warn("Failed to copy models to container")

    def restart_failed(self) -> None:
        self._logger.error("Failed to restart service")

    def health_check_failed(self) -> None:
        self._logger.error("Health check failed")

    def report_success(self) -> None:
        self._logger.section("Bootstrap Complete")
        self._logger.ok("llama.cpp is running")
        print()
        self._logger.info("Endpoints:")
        print("  API: http://localhost:8081")
        print("  Health: http://localhost:8081/health")
        print()
        self._logger.info("View logs: podman logs -f llama-coder")
