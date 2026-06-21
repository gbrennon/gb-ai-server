"""Wait and retry strategy."""

from dataclasses import dataclass
import time
from typing import Callable, TypeVar


T = TypeVar("T")


@dataclass
class WaitStrategy:
    """Exponential backoff retry strategy."""

    max_retries: int
    initial_interval_seconds: float = 1.0
    max_interval_seconds: float = 30.0
    backoff_multiplier: float = 2.0

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.initial_interval_seconds <= 0:
            raise ValueError("initial_interval_seconds must be positive")
        if self.max_interval_seconds <= 0:
            raise ValueError("max_interval_seconds must be positive")
        if self.backoff_multiplier <= 1:
            raise ValueError("backoff_multiplier must be > 1")

    def interval_for_attempt(self, attempt: int) -> float:
        """
        Calculate interval for given attempt number.

        Implements exponential backoff with max cap.

        Args:
            attempt: Zero-based attempt number.

        Returns:
            Interval in seconds.
        """
        interval = self.initial_interval_seconds * (
            self.backoff_multiplier ** attempt
        )
        return min(interval, self.max_interval_seconds)

    def wait_for_condition(
        self,
        condition: Callable[[], bool],
        on_retry: Callable[[int, float], None] | None = None,
    ) -> bool:
        """
        Wait until condition is true or max retries exceeded.

        Args:
            condition: Callable that returns True when ready.
            on_retry: Optional callback(attempt, interval) on retry.

        Returns:
            True if condition became true, False if max retries exceeded.
        """
        for attempt in range(self.max_retries + 1):
            if condition():
                return True

            if attempt < self.max_retries:
                interval = self.interval_for_attempt(attempt)
                if on_retry:
                    on_retry(attempt, interval)
                time.sleep(interval)

        return False

    def total_seconds(self) -> float:
        """
        Calculate total seconds for all retries.

        Rough estimate assuming max interval for later retries.

        Returns:
            Approximate total wait time in seconds.
        """
        total = 0.0
        for attempt in range(self.max_retries):
            total += self.interval_for_attempt(attempt)
        return total
