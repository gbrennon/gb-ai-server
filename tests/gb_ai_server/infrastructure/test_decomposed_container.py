"""Tests for the decomposed DI container and edge case error handling."""

from unittest.mock import MagicMock

from gb_ai_server.infrastructure.di.container import (
    InfrastructureRegistry,
    VerifierFactory,
    ComposeServiceFactory,
    ModelServiceFactory,
)
from gb_ai_server.application.services import (
    ModelCopierService,
    StartServicesService,
    RestartServicesService,
    StopServicesService,
    ListServicesService,
    ShowLogsService,
)
from gb_ai_server.application.dtos.requests import (
    CopyModelsRequest,
    StartServicesRequest,
    RestartServicesRequest,
    StopServicesRequest,
    ListServicesRequest,
    ShowLogsRequest,
)
from tests.gb_ai_server.conftest import make_logger_mock


class TestDecomposedContainer:
    def test_infrastructure_registry(self) -> None:
        registry = InfrastructureRegistry()
        assert registry.logger is not None
        assert registry.runtime_detector is not None
        assert registry.compose_detector is not None
        assert registry.http_client is not None

    def test_verifier_factory(self) -> None:
        registry = InfrastructureRegistry()
        factory = VerifierFactory(registry)
        
        prereq = factory.prerequisite_verifier()
        assert prereq is not None
        
        health = factory.health_verifier()
        assert health is not None

    def test_compose_service_factory(self) -> None:
        registry = InfrastructureRegistry()
        factory = ComposeServiceFactory(registry)
        lifecycle_mock = MagicMock()
        query_mock = MagicMock()

        assert factory.start_services(lifecycle_mock) is not None
        assert factory.stop_services(lifecycle_mock) is not None
        assert factory.restart_services(lifecycle_mock) is not None
        assert factory.list_services(query_mock) is not None
        assert factory.show_logs(query_mock) is not None

    def test_model_service_factory(self) -> None:
        registry = InfrastructureRegistry()
        factory = ModelServiceFactory(registry)
        downloader_mock = MagicMock()
        inspector_mock = MagicMock()
        operator_mock = MagicMock()
        registrar_mock = MagicMock()

        assert factory.model_downloader(downloader_mock) is not None
        assert factory.model_copier(inspector_mock, operator_mock) is not None
        assert factory.model_registrar(registrar_mock) is not None


class TestEdgeCasesNoneDependencies:
    def test_model_copier_none_deps(self) -> None:
        logger = make_logger_mock()
        # Pass None for inspector and operator
        service = ModelCopierService(logger, inspector=None, operator=None)
        
        request = CopyModelsRequest(
            entries=[("test_model", "test_model.bin", "http://url")],
            source_dir="/tmp",
            container_name="test-container",
            dest_dir="/models",
        )
        response = service.execute(request)
        
        assert response.results["test_model"] is False
        logger.error.assert_any_call("Container runtime inspector or operator is not available. Cannot copy models.")

    def test_start_services_none_deps(self) -> None:
        logger = make_logger_mock()
        service = StartServicesService(logger, compose_lifecycle=None)
        
        request = StartServicesRequest(compose_file="docker-compose.yml", services=("llama",))
        response = service.execute(request)
        
        assert response.success is False
        logger.error.assert_any_call("Compose lifecycle operator is not available. Cannot start services.")

    def test_restart_services_none_deps(self) -> None:
        logger = make_logger_mock()
        service = RestartServicesService(logger, compose_lifecycle=None)
        
        request = RestartServicesRequest(compose_file="docker-compose.yml", services=("llama",))
        response = service.execute(request)
        
        assert response.success is False
        logger.error.assert_any_call("Compose lifecycle operator is not available. Cannot restart services.")

    def test_stop_services_none_deps(self) -> None:
        logger = make_logger_mock()
        service = StopServicesService(logger, compose_lifecycle=None)
        
        request = StopServicesRequest(compose_file="docker-compose.yml")
        response = service.execute(request)
        
        assert response.success is False
        logger.error.assert_any_call("Compose lifecycle operator is not available. Cannot stop services.")

    def test_list_services_none_deps(self) -> None:
        logger = make_logger_mock()
        service = ListServicesService(logger, compose_query=None)
        
        request = ListServicesRequest(compose_file="docker-compose.yml")
        response = service.execute(request)
        
        assert response.success is False
        logger.error.assert_any_call("Compose query tool is not available. Cannot list services.")

    def test_show_logs_none_deps(self) -> None:
        logger = make_logger_mock()
        service = ShowLogsService(logger, compose_query=None)
        
        request = ShowLogsRequest(compose_file="docker-compose.yml", service="llama", follow=False)
        response = service.execute(request)
        
        assert response.success is False
        logger.error.assert_any_call("Compose query tool is not available. Cannot retrieve logs.")
