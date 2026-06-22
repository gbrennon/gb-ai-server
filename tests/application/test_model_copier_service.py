"""Tests for ModelCopierService (mocked outbound ports)."""

from pathlib import Path

from gb_ai_server.application.services import ModelCopierService
from gb_ai_server.application.dtos.requests import CopyModelsRequest
from tests.conftest import make_logger_mock, make_container_runtime_mock


class TestModelCopierService:
    def test_copies_models_to_running_container(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        runtime = make_container_runtime_mock(running=True)
        service = ModelCopierService(logger, runtime)

        model_file = tmp_path / "model.gguf"
        model_file.write_text("gguf-data")

        request = CopyModelsRequest(
            entries=[("test-model", "model.gguf", "https://example.com/model.gguf")],
            source_dir=str(tmp_path),
            container_name="llama-coder",
            dest_dir="/models",
        )
        response = service.execute(request)

        assert response.results == {"test-model": True}
        runtime.copy_to.assert_called_once()

    def test_skips_if_container_not_running(self) -> None:
        logger = make_logger_mock()
        runtime = make_container_runtime_mock(running=False)
        service = ModelCopierService(logger, runtime)

        request = CopyModelsRequest(
            entries=[("test-model", "model.gguf", "https://example.com/model.gguf")],
            source_dir="/tmp/models",
            container_name="llama-coder",
        )
        response = service.execute(request)

        assert response.results == {"test-model": False}
        runtime.copy_to.assert_not_called()

    def test_skips_if_model_file_missing(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        runtime = make_container_runtime_mock(running=True)
        service = ModelCopierService(logger, runtime)

        request = CopyModelsRequest(
            entries=[("missing", "nonexistent.gguf", "https://example.com/n.gguf")],
            source_dir=str(tmp_path),
            container_name="llama-coder",
        )
        response = service.execute(request)

        assert response.results == {"missing": False}
        runtime.copy_to.assert_not_called()

    def test_reports_copy_failure(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        runtime = make_container_runtime_mock(running=True)
        runtime.copy_to.return_value.success = False
        service = ModelCopierService(logger, runtime)

        model_file = tmp_path / "model.gguf"
        model_file.write_text("data")

        request = CopyModelsRequest(
            entries=[("test", "model.gguf", "https://example.com/model.gguf")],
            source_dir=str(tmp_path),
            container_name="llama-coder",
        )
        response = service.execute(request)

        assert response.results == {"test": False}

    def test_logs_stderr_on_copy_failure(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        from gb_ai_server.domain import CommandResult
        runtime = make_container_runtime_mock(running=True)
        runtime.copy_to.return_value = CommandResult(
            returncode=1, stdout="", stderr="permission denied", success=False
        )
        service = ModelCopierService(logger, runtime)

        model_file = tmp_path / "model.gguf"
        model_file.write_text("data")

        request = CopyModelsRequest(
            entries=[("test", "model.gguf", "https://example.com/model.gguf")],
            source_dir=str(tmp_path),
            container_name="llama-coder",
        )
        service.execute(request)

        logger.debug.assert_called_with("permission denied")
