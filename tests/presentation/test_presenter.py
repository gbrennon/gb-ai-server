"""Tests for presentation layer BootstrapPresenter."""

from unittest.mock import MagicMock

from gb_ai_server.presentation.presenter import BootstrapPresenter


class TestBootstrapPresenter:
    def make_logger(self) -> MagicMock:
        return MagicMock()

    def test_no_models_configured_logs_error(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).no_models_configured()
        logger.error.assert_called_once_with("No models configured")

    def test_prerequisites_failed_logs_error(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).prerequisites_failed()
        logger.error.assert_called_once_with("Prerequisites not met")

    def test_detection_failed_logs_error(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).detection_failed()
        logger.error.assert_called_once_with("Failed to detect compose tool or runtime")

    def test_skipping_download_logs_info(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).skipping_download()
        logger.info.assert_called_once_with("Skipping model download (--skip-download)")

    def test_all_downloads_failed_logs_warn(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).all_downloads_failed()
        logger.warn.assert_called_once_with("All model downloads failed")

    def test_start_services_failed_logs_error(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).start_services_failed()
        logger.error.assert_called_once_with("Failed to start services")

    def test_copy_models_failed_logs_warn(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).copy_models_failed()
        logger.warn.assert_called_once_with("Failed to copy models to container")

    def test_restart_failed_logs_error(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).restart_failed()
        logger.error.assert_called_once_with("Failed to restart service")

    def test_health_check_failed_logs_error(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).health_check_failed()
        logger.error.assert_called_once_with("Health check failed")

    def test_report_success_calls_all_outputs(self) -> None:
        logger = self.make_logger()
        BootstrapPresenter(logger).report_success()
        logger.section.assert_called_once_with("Bootstrap Complete")
        logger.ok.assert_called_once_with("llama.cpp is running")
