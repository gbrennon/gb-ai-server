"""Tests for DI container (factory methods return correct types)."""

from gb_ai_server.infrastructure.di.container import Container
from gb_ai_server.application.services import (
    PrerequisiteVerifierService,
    HealthVerifierService,
)
from gb_ai_server.infrastructure.logging import TerminalLogger
from tests.gb_ai_server.conftest import make_lifecycle_mock, make_query_mock, make_inspector_mock, make_operator_mock, make_model_downloader_mock


class TestContainer:
    def test_creates_default_dependencies(self) -> None:
        container = Container()
        assert isinstance(container.logger, TerminalLogger)

    def test_properties(self) -> None:
        container = Container()
        assert container.runtime_detector is not None
        assert container.compose_detector is not None
        assert container.http_client is not None

    def test_prerequisite_verifier(self) -> None:
        container = Container()
        service = container.prerequisite_verifier()
        assert isinstance(service, PrerequisiteVerifierService)

    def test_health_verifier(self) -> None:
        container = Container()
        service = container.health_verifier()
        assert isinstance(service, HealthVerifierService)

    def test_start_services(self) -> None:
        container = Container()
        lifecycle = make_lifecycle_mock()
        service = container.start_services(lifecycle)
        assert service.compose_lifecycle is lifecycle

    def test_stop_services(self) -> None:
        container = Container()
        lifecycle = make_lifecycle_mock()
        service = container.stop_services(lifecycle)
        assert service.compose_lifecycle is lifecycle

    def test_restart_services(self) -> None:
        container = Container()
        lifecycle = make_lifecycle_mock()
        service = container.restart_services(lifecycle)
        assert service.compose_lifecycle is lifecycle

    def test_list_services(self) -> None:
        container = Container()
        query = make_query_mock()
        service = container.list_services(query)
        assert service.compose_query is query

    def test_show_logs(self) -> None:
        container = Container()
        query = make_query_mock()
        service = container.show_logs(query)
        assert service.compose_query is query

    def test_model_copier(self) -> None:
        container = Container()
        inspector = make_inspector_mock()
        operator = make_operator_mock()
        service = container.model_copier(inspector, operator)
        assert service._inspector is inspector
        assert service._operator is operator

    def test_model_downloader(self) -> None:
        container = Container()
        downloader = make_model_downloader_mock()
        service = container.model_downloader(downloader)
        assert service.downloader is downloader
