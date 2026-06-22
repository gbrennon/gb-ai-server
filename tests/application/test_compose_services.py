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
from tests.conftest import make_logger_mock, make_compose_tool_mock


class TestStartServicesService:
    def test_starts_services(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(up_ok=True)
        service = StartServicesService(logger, compose)

        response = service.execute(
            StartServicesRequest(compose_file="compose.yml", services=("web",))
        )

        assert response.success is True
        compose.up.assert_called_with(Path("compose.yml"), "web", detach=True)

    def test_fails_when_up_fails(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(up_ok=False)
        service = StartServicesService(logger, compose)

        response = service.execute(
            StartServicesRequest(compose_file="compose.yml")
        )

        assert response.success is False


class TestStopServicesService:
    def test_stops_services(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(down_ok=True)
        service = StopServicesService(logger, compose)

        response = service.execute(
            StopServicesRequest(compose_file="compose.yml")
        )

        assert response.success is True
        compose.down.assert_called_with(Path("compose.yml"))

    def test_fails_gracefully(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(down_ok=False)
        service = StopServicesService(logger, compose)

        response = service.execute(
            StopServicesRequest(compose_file="compose.yml")
        )

        assert response.success is False


class TestRestartServicesService:
    def test_restarts_services(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(restart_ok=True)
        service = RestartServicesService(logger, compose)

        response = service.execute(
            RestartServicesRequest(compose_file="compose.yml", services=("web",))
        )

        assert response.success is True
        compose.restart.assert_called_with(Path("compose.yml"), "web")

    def test_fails_when_restart_fails(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(restart_ok=False)
        service = RestartServicesService(logger, compose)

        response = service.execute(
            RestartServicesRequest(compose_file="compose.yml")
        )

        assert response.success is False


class TestListServicesService:
    def test_lists_services(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(ps_ok=True)
        service = ListServicesService(logger, compose)

        response = service.execute(
            ListServicesRequest(compose_file="compose.yml")
        )

        assert response.success is True
        assert "CONTAINER ID" in (response.output or "")
        compose.ps.assert_called_with(Path("compose.yml"))

    def test_returns_false_when_no_services(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(ps_ok=False)
        service = ListServicesService(logger, compose)

        response = service.execute(
            ListServicesRequest(compose_file="compose.yml")
        )

        assert response.success is False


class TestShowLogsService:
    def test_shows_logs(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(logs_ok=True)
        service = ShowLogsService(logger, compose)

        response = service.execute(
            ShowLogsRequest(compose_file="compose.yml", service="web")
        )

        assert response.success is True
        assert response.output == "[INFO] Server started"
        compose.logs.assert_called_with(Path("compose.yml"), service="web", follow=False)

    def test_returns_false_when_logs_fail(self) -> None:
        logger = make_logger_mock()
        compose = make_compose_tool_mock(logs_ok=False)
        service = ShowLogsService(logger, compose)

        response = service.execute(
            ShowLogsRequest(compose_file="compose.yml")
        )

        assert response.success is False
