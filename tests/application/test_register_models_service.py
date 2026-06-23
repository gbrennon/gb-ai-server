"""Tests for RegisterModelsService (mocked outbound ports)."""

from gb_ai_server.application.services import RegisterModelsService
from gb_ai_server.application.dtos.requests import RegisterModelsRequest
from tests.conftest import make_logger_mock


class TestRegisterModelsService:
    def test_registers_all_models(self) -> None:
        logger = make_logger_mock()
        registrar = make_registrar_mock(success=True)
        service = RegisterModelsService(logger, registrar)

        request = RegisterModelsRequest(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
        )
        response = service.execute(request)

        assert response.success is True
        assert response.registered_models == ["model-a"]
        registrar.register_models.assert_called_once()

    def test_registers_multiple_models(self) -> None:
        logger = make_logger_mock()
        registrar = make_registrar_mock(success=True)
        service = RegisterModelsService(logger, registrar)

        models = [
            ("model-a", "a.gguf", 8081, "llama-coder"),
            ("model-b", "b.gguf", 8082, "llama-qwen3"),
        ]
        request = RegisterModelsRequest(models=models)
        response = service.execute(request)

        assert response.success is True
        assert response.registered_models == ["model-a", "model-b"]

    def test_reports_failure_when_registrar_fails(self) -> None:
        logger = make_logger_mock()
        registrar = make_registrar_mock(success=False)
        service = RegisterModelsService(logger, registrar)

        request = RegisterModelsRequest(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
        )
        response = service.execute(request)

        assert response.success is False

    def test_reports_failure_when_no_models(self) -> None:
        logger = make_logger_mock()
        registrar = make_registrar_mock(success=True)
        service = RegisterModelsService(logger, registrar)

        request = RegisterModelsRequest(models=[])
        response = service.execute(request)

        assert response.success is False
        assert response.registered_models == []
        registrar.register_models.assert_not_called()

    def test_forwards_provider_base_url(self) -> None:
        logger = make_logger_mock()
        registrar = make_registrar_mock(success=True)
        service = RegisterModelsService(logger, registrar)

        request = RegisterModelsRequest(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
            provider_base_url="http://localhost:8081",
        )
        service.execute(request)

        registrar.register_models.assert_called_with(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
            provider_base_url="http://localhost:8081",
        )


def make_registrar_mock(success: bool = True):
    """Create a mock ModelRegistrar."""
    from unittest.mock import MagicMock

    r = MagicMock()
    r.register_models.return_value = success
    r.is_registered.return_value = success
    return r
