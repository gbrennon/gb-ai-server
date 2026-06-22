"""Tests for WaitStrategy domain logic."""

from unittest.mock import patch
import pytest
from gb_ai_server.domain import WaitStrategy


class TestValidation:
    def test_negative_max_retries_raises(self) -> None:
        with pytest.raises(ValueError, match="max_retries"):
            WaitStrategy(max_retries=-1)

    def test_zero_initial_interval_raises(self) -> None:
        with pytest.raises(ValueError, match="initial_interval"):
            WaitStrategy(max_retries=3, initial_interval_seconds=0)

    def test_negative_initial_interval_raises(self) -> None:
        with pytest.raises(ValueError, match="initial_interval"):
            WaitStrategy(max_retries=3, initial_interval_seconds=-1)

    def test_backoff_must_be_greater_than_one(self) -> None:
        with pytest.raises(ValueError, match="backoff_multiplier"):
            WaitStrategy(max_retries=3, backoff_multiplier=1)

    def test_backoff_below_one_raises(self) -> None:
        with pytest.raises(ValueError, match="backoff_multiplier"):
            WaitStrategy(max_retries=3, backoff_multiplier=0.5)

    def test_max_interval_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="max_interval_seconds"):
            WaitStrategy(max_retries=3, max_interval_seconds=0)

    def test_max_interval_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="max_interval_seconds"):
            WaitStrategy(max_retries=3, max_interval_seconds=-1)


class TestIntervalForAttempt:
    def test_first_attempt(self) -> None:
        w = WaitStrategy(max_retries=3, initial_interval_seconds=1.0)
        assert w.interval_for_attempt(0) == 1.0

    def test_backoff(self) -> None:
        w = WaitStrategy(max_retries=3, initial_interval_seconds=1.0)
        assert w.interval_for_attempt(1) == 2.0
        assert w.interval_for_attempt(2) == 4.0

    def test_capped_by_max_interval(self) -> None:
        w = WaitStrategy(
            max_retries=10,
            initial_interval_seconds=1.0,
            max_interval_seconds=3.0,
        )
        assert w.interval_for_attempt(5) == 3.0


class TestTotalSeconds:
    def test_no_retries(self) -> None:
        w = WaitStrategy(max_retries=0)
        assert w.total_seconds() == 0.0

    def test_some_retries(self) -> None:
        w = WaitStrategy(max_retries=2, initial_interval_seconds=1.0)
        assert w.total_seconds() == pytest.approx(1.0 + 2.0)


class TestWaitForCondition:
    def test_returns_true_when_condition_immediately_true(self) -> None:
        w = WaitStrategy(max_retries=3)
        with patch("time.sleep") as mock_sleep:
            result = w.wait_for_condition(lambda: True)
            assert result is True
            mock_sleep.assert_not_called()

    def test_returns_false_when_condition_never_true(self) -> None:
        w = WaitStrategy(max_retries=2, initial_interval_seconds=0.01)
        with patch("time.sleep"):
            result = w.wait_for_condition(lambda: False)
            assert result is False

    def test_condition_becomes_true_after_retries(self) -> None:
        state = {"call_count": 0}

        def condition() -> bool:
            state["call_count"] += 1
            return state["call_count"] >= 2

        w = WaitStrategy(max_retries=3, initial_interval_seconds=0.01)
        with patch("time.sleep"):
            result = w.wait_for_condition(condition)
            assert result is True

    def test_calls_on_retry_callback(self) -> None:
        calls: list[tuple[int, float]] = []
        w = WaitStrategy(max_retries=2, initial_interval_seconds=0.01)

        with patch("time.sleep"):
            w.wait_for_condition(
                lambda: False,
                on_retry=lambda attempt, interval: calls.append((attempt, interval)),
            )

        assert len(calls) == 2
        assert calls[0] == (0, 0.01)
        assert calls[1] == (1, 0.02)

    def test_does_not_call_on_retry_on_success(self) -> None:
        calls: list[tuple[int, float]] = []

        w = WaitStrategy(max_retries=2)

        with patch("time.sleep"):
            w.wait_for_condition(
                lambda: True,
                on_retry=lambda attempt, interval: calls.append((attempt, interval)),
            )

        assert calls == []
