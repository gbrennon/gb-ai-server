"""Tests for ModelCopierService (mocked outbound ports)."""

from unittest.mock import MagicMock
from pathlib import Path

from gb_ai_server.application.services import ModelCopierService
from gb_ai_server.application.dtos.requests import CopyModelsRequest
from gb_ai_server.domain import CommandResult
from tests.gb_ai_server.conftest import make_logger_mock


def _make_inspector_mock(running: bool = True) -> MagicMock:
    ins = MagicMock()
    ins.is_running.return_value = running
    return ins


def _make_operator_mock() -> MagicMock:
    op = MagicMock()
    op.copy_to.return_value = CommandResult(
        returncode=0, stdout="", stderr="", success=True
    )
    return op


class TestModelCopierService:
    def test_copies_models_to_running_container(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        inspector = _make_inspector_mock(running=True)
        operator = _make_operator_mock()
        service = ModelCopierService(logger, inspector, operator)

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
        operator.copy_to.assert_called_once()

    def test_skips_if_container_not_running(self) -> None:
        logger = make_logger_mock()
        inspector = _make_inspector_mock(running=False)
        operator = _make_operator_mock()
        service = ModelCopierService(logger, inspector, operator)

        request = CopyModelsRequest(
            entries=[("test-model", "model.gguf", "https://example.com/model.gguf")],
            source_dir="/tmp/models",
            container_name="llama-coder",
        )
        response = service.execute(request)

        assert response.results == {"test-model": False}
        operator.copy_to.assert_not_called()

    def test_skips_if_model_file_missing(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        inspector = _make_inspector_mock(running=True)
        operator = _make_operator_mock()
        service = ModelCopierService(logger, inspector, operator)

        request = CopyModelsRequest(
            entries=[("missing", "nonexistent.gguf", "https://example.com/n.gguf")],
            source_dir=str(tmp_path),
            container_name="llama-coder",
        )
        response = service.execute(request)

        assert response.results == {"missing": False}
        operator.copy_to.assert_not_called()

    def test_reports_copy_failure(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        inspector = _make_inspector_mock(running=True)
        operator = _make_operator_mock()
        operator.copy_to.return_value.success = False
        service = ModelCopierService(logger, inspector, operator)

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
        inspector = _make_inspector_mock(running=True)
        operator = _make_operator_mock()
        operator.copy_to.return_value = CommandResult(
            returncode=1, stdout="", stderr="permission denied", success=False
        )
        service = ModelCopierService(logger, inspector, operator)

        model_file = tmp_path / "model.gguf"
        model_file.write_text("data")

        request = CopyModelsRequest(
            entries=[("test", "model.gguf", "https://example.com/model.gguf")],
            source_dir=str(tmp_path),
            container_name="llama-coder",
        )
        service.execute(request)

        logger.debug.assert_called_with("permission denied")
