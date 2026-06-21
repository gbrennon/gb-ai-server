"""Health check strategy and URL generation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthCheckStrategy:
    """Health check configuration for a service."""

    host: str = "localhost"
    path: str = "/health"

    def url(self, port: int) -> str:
        """
        Generate health check URL for given port.

        Args:
            port: Service port.

        Returns:
            Full health check URL (e.g., "http://localhost:8081/health").
        """
        return f"http://{self.host}:{port}{self.path}"


class HealthCheckTimeoutCalculator:
    """Calculate health check timeouts based on model characteristics."""

    BASE_SECONDS: int = 20
    PER_GB_SECONDS: int = 2

    @classmethod
    def timeout_for_model(cls, model_size_gb: int) -> int:
        """
        Calculate startup timeout for model.

        Larger models take longer to load.
        Heuristic: 20s base + 2s per GB

        Args:
            model_size_gb: Model size in gigabytes.

        Returns:
            Timeout in seconds.

        Raises:
            ValueError: If size is negative.
        """
        if model_size_gb < 0:
            raise ValueError("Model size cannot be negative")

        return cls.BASE_SECONDS + (model_size_gb // cls.PER_GB_SECONDS)

    @classmethod
    def max_retries(
        cls,
        timeout_seconds: int,
        interval_seconds: int = 5,
    ) -> int:
        """
        Calculate max retries for given timeout and interval.

        Args:
            timeout_seconds: Total timeout in seconds.
            interval_seconds: Retry interval in seconds.

        Returns:
            Maximum number of retries.

        Raises:
            ValueError: If timeout <= 0 or interval <= 0.
        """
        if timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        if interval_seconds <= 0:
            raise ValueError("Interval must be positive")

        return timeout_seconds // interval_seconds
