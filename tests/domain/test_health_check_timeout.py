"""Tests for HealthCheckTimeoutCalculator domain logic."""

import pytest
from gb_ai_server.domain import HealthCheckTimeoutCalculator


class TestTimeoutForModel:
    def test_zero_gb(self) -> None:
        assert HealthCheckTimeoutCalculator.timeout_for_model(0) == 20

    def test_small_model(self) -> None:
        assert HealthCheckTimeoutCalculator.timeout_for_model(7) == 23

    def test_large_model(self) -> None:
        assert HealthCheckTimeoutCalculator.timeout_for_model(70) == 55

    def test_raises_on_negative(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            HealthCheckTimeoutCalculator.timeout_for_model(-1)


class TestMaxRetries:
    def test_basic(self) -> None:
        assert HealthCheckTimeoutCalculator.max_retries(60, 5) == 12

    def test_exact_division(self) -> None:
        assert HealthCheckTimeoutCalculator.max_retries(30, 10) == 3

    def test_raises_on_zero_timeout(self) -> None:
        with pytest.raises(ValueError, match="Timeout must be positive"):
            HealthCheckTimeoutCalculator.max_retries(0, 5)

    def test_raises_on_negative_timeout(self) -> None:
        with pytest.raises(ValueError, match="Timeout must be positive"):
            HealthCheckTimeoutCalculator.max_retries(-1, 5)

    def test_raises_on_zero_interval(self) -> None:
        with pytest.raises(ValueError, match="Interval must be positive"):
            HealthCheckTimeoutCalculator.max_retries(60, 0)

    def test_raises_on_negative_interval(self) -> None:
        with pytest.raises(ValueError, match="Interval must be positive"):
            HealthCheckTimeoutCalculator.max_retries(60, -1)
