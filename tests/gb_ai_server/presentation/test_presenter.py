"""Tests for presentation layer presenter classes."""

from unittest.mock import MagicMock

from gb_ai_server.presentation.presenter import (
    DownloadPresenter,
    ModelActionPresenter,
    ModelSelectionPresenter,
    PrerequisitePresenter,
    RegistrationPresenter,
    ServiceLifecyclePresenter,
)


def make_logger() -> MagicMock:
    return MagicMock()


class TestPrerequisitePresenter:
    def test_no_models_configured_logs_error(self) -> None:
        logger = make_logger()
        PrerequisitePresenter(logger).no_models_configured()
        logger.error.assert_called_once_with("No models configured")

    def test_prerequisites_failed_logs_error(self) -> None:
        logger = make_logger()
        PrerequisitePresenter(logger).prerequisites_failed()
        logger.error.assert_called_once_with("Prerequisites not met")

    def test_detection_failed_logs_error(self) -> None:
        logger = make_logger()
        PrerequisitePresenter(logger).detection_failed()
        logger.error.assert_called_once_with("Failed to detect compose tool or runtime")

    def test_skipping_download_logs_info(self) -> None:
        logger = make_logger()
        PrerequisitePresenter(logger).skipping_download()
        logger.info.assert_called_once_with("Skipping model download (--skip-download)")


class TestDownloadPresenter:
    def test_all_downloads_failed_logs_warn(self) -> None:
        logger = make_logger()
        DownloadPresenter(logger).all_downloads_failed()
        logger.warn.assert_called_once_with("All model downloads failed")

    def test_copy_models_failed_logs_warn(self) -> None:
        logger = make_logger()
        DownloadPresenter(logger).copy_models_failed()
        logger.warn.assert_called_once_with("Failed to copy models to container")


class TestServiceLifecyclePresenter:
    def test_start_services_failed_logs_error(self) -> None:
        logger = make_logger()
        ServiceLifecyclePresenter(logger).start_services_failed()
        logger.error.assert_called_once_with("Failed to start services")

    def test_restart_failed_logs_error(self) -> None:
        logger = make_logger()
        ServiceLifecyclePresenter(logger).restart_failed()
        logger.error.assert_called_once_with("Failed to restart service")

    def test_health_check_failed_logs_error(self) -> None:
        logger = make_logger()
        ServiceLifecyclePresenter(logger).health_check_failed()
        logger.error.assert_called_once_with("Health check failed")

    def test_report_success_calls_all_outputs(self) -> None:
        logger = make_logger()
        ServiceLifecyclePresenter(logger).report_success()
        logger.ok.assert_called_once_with("llama.cpp is running")


class TestModelSelectionPresenter:
    def test_model_not_found(self) -> None:
        logger = make_logger()
        ModelSelectionPresenter(logger).model_not_found("fake")
        logger.error.assert_called_once()

    def test_model_already_running(self) -> None:
        logger = make_logger()
        ModelSelectionPresenter(logger).model_already_running("test-model")
        logger.ok.assert_called_once()

    def test_switching_model(self) -> None:
        logger = make_logger()
        ModelSelectionPresenter(logger).switching_model("old", "new")
        logger.info.assert_called()

    def test_model_not_available(self) -> None:
        logger = make_logger()
        ModelSelectionPresenter(logger).model_not_available("m", "f.gguf")
        logger.warn.assert_called_once()


class TestModelActionPresenter:
    def test_stopping_previous(self) -> None:
        logger = make_logger()
        ModelActionPresenter(logger).stopping_previous("test-model")
        logger.info.assert_called_once()

    def test_starting_model(self) -> None:
        logger = make_logger()
        ModelActionPresenter(logger).starting_model("test-model")
        logger.info.assert_called_once()


class TestRegistrationPresenter:
    def test_models_registered(self) -> None:
        logger = make_logger()
        RegistrationPresenter(logger).models_registered(["test-model"])
        logger.ok.assert_called_once()

    def test_registration_failed(self) -> None:
        logger = make_logger()
        RegistrationPresenter(logger).registration_failed()
        logger.warn.assert_called_once()
