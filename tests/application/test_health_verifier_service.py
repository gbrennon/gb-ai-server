"""Tests for HealthVerifierService (mocked outbound ports)."""

from unittest.mock import patch

from gb_ai_server.application.services import HealthVerifierService
from gb_ai_server.application.dtos.requests import VerifyHealthRequest
from tests.conftest import make_logger_mock, make_http_client_mock


class TestHealthVerifierService:
    def test_returns_true_when_all_healthy(self) -> None:
        logger = make_logger_mock()
        http = make_http_client_mock(healthy=True)
        service = HealthVerifierService(logger, http)

        with patch("time.sleep"):
            response = service.execute(
                VerifyHealthRequest(ports=(8081,), timeout_seconds=10, interval_seconds=1)
            )

        assert response.success is True

    def test_returns_false_when_unhealthy(self) -> None:
        logger = make_logger_mock()
        http = make_http_client_mock(healthy=False)
        service = HealthVerifierService(logger, http)

        with patch("time.sleep"):
            response = service.execute(
                VerifyHealthRequest(ports=(8081,), timeout_seconds=1, interval_seconds=1)
            )

        assert response.success is False

    def test_checks_multiple_ports(self) -> None:
        logger = make_logger_mock()
        http = make_http_client_mock(healthy=True)
        service = HealthVerifierService(logger, http)

        with patch("time.sleep"):
            response = service.execute(
                VerifyHealthRequest(
                    ports=(8081, 8082), timeout_seconds=10, interval_seconds=1
                )
            )

        assert response.success is True
        assert http.get.call_count >= 2

    def test_reports_unhealthy_when_one_port_fails(self) -> None:
        logger = make_logger_mock()
        http = make_http_client_mock(healthy=False)
        service = HealthVerifierService(logger, http)

        with patch("time.sleep"):
            response = service.execute(
                VerifyHealthRequest(
                    ports=(8081, 8082), timeout_seconds=1, interval_seconds=1
                )
            )

        assert response.success is False
