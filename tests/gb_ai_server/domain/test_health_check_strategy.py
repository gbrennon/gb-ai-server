"""Tests for HealthCheckStrategy domain logic."""

from gb_ai_server.domain import HealthCheckStrategy


class TestUrl:
    def test_default_host_and_path(self) -> None:
        strategy = HealthCheckStrategy()
        assert strategy.url(8081) == "http://localhost:8081/health"

    def test_custom_host(self) -> None:
        strategy = HealthCheckStrategy(host="192.168.1.100")
        assert strategy.url(8081) == "http://192.168.1.100:8081/health"

    def test_custom_path(self) -> None:
        strategy = HealthCheckStrategy(path="/api/health")
        assert strategy.url(8081) == "http://localhost:8081/api/health"

    def test_different_port(self) -> None:
        strategy = HealthCheckStrategy()
        assert strategy.url(9090) == "http://localhost:9090/health"
