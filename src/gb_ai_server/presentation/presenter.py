"""Console output formatting for the bootstrap CLI.

Decomposed into focused presenter classes, each with ≤5 public methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gb_ai_server.application.utils import print_section

if TYPE_CHECKING:
    from gb_ai_server.application.ports.outbound import Logger


class PrerequisitePresenter:
    """Output for environment checks and model config validation."""

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


class DownloadPresenter:
    """Output for model download and copy steps."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def all_downloads_failed(self) -> None:
        self._logger.warn("All model downloads failed")

    def copy_models_failed(self) -> None:
        self._logger.warn("Failed to copy models to container")


class ServiceLifecyclePresenter:
    """Output for service start, restart, health, and success."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def start_services_failed(self) -> None:
        self._logger.error("Failed to start services")

    def restart_failed(self) -> None:
        self._logger.error("Failed to restart service")

    def health_check_failed(self) -> None:
        self._logger.error("Health check failed")

    def report_success(self, port: int = 8081) -> None:
        print_section("Bootstrap Complete")
        self._logger.ok("llama.cpp is running")
        print()
        self._logger.info("Endpoints:")
        print(f"  API: http://localhost:{port}")
        print(f"  Health: http://localhost:{port}/health")
        print()
        self._logger.info("View logs: podman logs -f llama-coder")


class ModelSelectionPresenter:
    """Output for model resolution and switching."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def model_not_found(self, model_name: str) -> None:
        self._logger.error(f"Model '{model_name}' not found in configuration")

    def model_not_available(self, display_name: str, filename: str) -> None:
        self._logger.warn(
            f"Model '{display_name}' ({filename}) not found locally — "
            f"skipping Cline registration"
        )

    def list_available_models(self, models: list[tuple[str, str]]) -> None:
        print_section("Available Models")
        for display_name, filename in models:
            print(f"  {display_name:30s} {filename}")

    def model_already_running(self, display_name: str) -> None:
        self._logger.ok(f"'{display_name}' is already running — nothing to do")

    def switching_model(self, old_model: str, new_model: str) -> None:
        self._logger.info(f"Switching from '{old_model}' to '{new_model}'")
        self._logger.info("Stopping current container...")


class ModelActionPresenter:
    """Output for model start/stop actions."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def stopping_previous(self, model_name: str) -> None:
        self._logger.info(f"Stopping '{model_name}' before starting new model")

    def starting_model(self, display_name: str) -> None:
        self._logger.info(f"Starting '{display_name}'...")


class RegistrationPresenter:
    """Output for Cline model registration."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def models_registered(self, registered_models: list[str]) -> None:
        self._logger.ok(
            f"Registered {len(registered_models)} model(s) with Cline: "
            f"{', '.join(registered_models)}"
        )

    def registration_failed(self) -> None:
        self._logger.warn("Failed to register models with Cline")
