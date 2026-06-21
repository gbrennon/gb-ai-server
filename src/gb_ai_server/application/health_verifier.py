"""Health check verification service."""

from typing import Sequence

from ..core import Logger, Command
from ..domain import (
    HealthCheckStrategy,
    HealthCheckTimeoutCalculator,
    WaitStrategy,
)


class HealthVerifier:
    """Verify service health via HTTP endpoints."""

    def __init__(self, logger: Logger) -> None:
        """
        Initialize health verifier.

        Args:
            logger: Logger instance.
        """
        self.logger = logger

    def verify_health(
        self,
        ports: Sequence[int],
        timeout_seconds: int = 60,
        interval_seconds: int = 5,
    ) -> bool:
        """
        Verify services are healthy on given ports.

        Args:
            ports: Port numbers to check.
            timeout_seconds: Total timeout in seconds.
            interval_seconds: Retry interval in seconds.

        Returns:
            True if all services healthy.
        """
        self.logger.section("Health Verification")

        strategy = HealthCheckStrategy()
        all_healthy = True

        for port in ports:
            endpoint = strategy.url(port)
            if not self.verify_endpoint(
                endpoint,
                timeout_seconds,
                interval_seconds,
            ):
                all_healthy = False

        return all_healthy

    def verify_endpoint(
        self,
        endpoint: str,
        timeout_seconds: int = 60,
        interval_seconds: int = 5,
    ) -> bool:
        """
        Verify single endpoint is healthy.

        Args:
            endpoint: Full HTTP endpoint URL.
            timeout_seconds: Total timeout in seconds.
            interval_seconds: Retry interval in seconds.

        Returns:
            True if endpoint became healthy.
        """
        self.logger.info(f"Checking {endpoint}...")

        wait_strategy = WaitStrategy(
            max_retries=timeout_seconds // interval_seconds,
            initial_interval_seconds=float(interval_seconds),
        )

        def is_healthy() -> bool:
            result = Command.run(
                "curl",
                "-sf",
                endpoint,
                capture_output=True,
            )
            return result.success

        def on_retry(attempt: int, interval: float) -> None:
            self.logger.debug(
                f"Retry {attempt}: waiting {interval}s before next check"
            )

        if wait_strategy.wait_for_condition(is_healthy, on_retry=on_retry):
            self.logger.ok(f"Service on {endpoint} is healthy")
            return True
        else:
            self.logger.warn(
                f"Service on {endpoint} did not become healthy in time"
            )
            return False
