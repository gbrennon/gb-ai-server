"""Tests for compose-based services (mocked outbound ports)."""

from pathlib import Path


from gb_ai_server.application.services import (
    StartServicesService,
    StopServicesService,
    RestartServicesService,
    ListServicesService,
    ShowLogsService,
)
from gb_ai_server.application.dtos.requests import (
    StartServicesRequest,
    StopServicesRequest,
    RestartServicesRequest,
    ListServicesRequest,
    ShowLogsRequest,
)
from tests.gb_ai_server.conftest import make_logger_mock, make_lifecycle_mock, make_query_mock


class TestStartServicesService:
    def test_starts_services(self) -> None:
        logger = make_logger_mock()
        lifecycle = make_lifecycle_mock(up_ok=True)
        service = StartServicesService(logger, lifecycle)

        response = service.execute(
            StartServicesRequest(compose_file="compose.yml", services=("web",))
        )

        assert response.success is True
        lifecycle.up.assert_called_with(Path("compose.yml"), "web", detach=True)

    def test_fails_when_up_fails(self) -> None:
        logger = make_logger_mock()
        lifecycle = make_lifecycle_mock(up_ok=False)
        service = StartServicesService(logger, lifecycle)

        response = service.execute(
            StartServicesRequest(compose_file="compose.yml")
        )

        assert response.success is False


class TestStopServicesService:
    def test_stops_services(self) -> None:
        logger = make_logger_mock()
        lifecycle = make_lifecycle_mock(down_ok=True)
        service = StopServicesService(logger, lifecycle)

        response = service.execute(
            StopServicesRequest(compose_file="compose.yml")
        )

        assert response.success is True
        lifecycle.down.assert_called_with(Path("compose.yml"))

    def test_fails_gracefully(self) -> None:
        logger = make_logger_mock()
        lifecycle = make_lifecycle_mock(down_ok=False)
        service = StopServicesService(logger, lifecycle)

        response = service.execute(
            StopServicesRequest(compose_file="compose.yml")
        )

        assert response.success is False


class TestRestartServicesService:
    def test_restarts_services(self) -> None:
        logger = make_logger_mock()
        lifecycle = make_lifecycle_mock(restart_ok=True)
        service = RestartServicesService(logger, lifecycle)

        response = service.execute(
            RestartServicesRequest(compose_file="compose.yml", services=("web",))
        )

        assert response.success is True
        lifecycle.restart.assert_called_with(Path("compose.yml"), "web")

    def test_fails_when_restart_fails(self) -> None:
        logger = make_logger_mock()
        lifecycle = make_lifecycle_mock(restart_ok=False)
        service = RestartServicesService(logger, lifecycle)

        response = service.execute(
            RestartServicesRequest(compose_file="compose.yml")
        )

        assert response.success is False


class TestListServicesService:
    def test_lists_services(self) -> None:
        logger = make_logger_mock()
        query = make_query_mock(ps_ok=True)
        service = ListServicesService(logger, query)

        response = service.execute(
            ListServicesRequest(compose_file="compose.yml")
        )

        assert response.success is True
        assert "CONTAINER ID" in (response.output or "")
        query.ps.assert_called_with(Path("compose.yml"))

    def test_returns_false_when_no_services(self) -> None:
        logger = make_logger_mock()
        query = make_query_mock(ps_ok=False)
        service = ListServicesService(logger, query)

        response = service.execute(
            ListServicesRequest(compose_file="compose.yml")
        )

        assert response.success is False


class TestShowLogsService:
    def test_shows_logs(self) -> None:
        logger = make_logger_mock()
        query = make_query_mock(logs_ok=True)
        service = ShowLogsService(logger, query)

        response = service.execute(
            ShowLogsRequest(compose_file="compose.yml", service="web")
        )

        assert response.success is True
        assert response.output == "[INFO] Server started"
        query.logs.assert_called_with(Path("compose.yml"), service="web", follow=False)

    def test_returns_false_when_logs_fail(self) -> None:
        logger = make_logger_mock()
        query = make_query_mock(logs_ok=False)
        service = ShowLogsService(logger, query)

        response = service.execute(
            ShowLogsRequest(compose_file="compose.yml")
        )

        assert response.success is False
