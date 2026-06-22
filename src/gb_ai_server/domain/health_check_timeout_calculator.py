"""Calculate health check timeouts based on model characteristics."""


class HealthCheckTimeoutCalculator:
    """Calculate health check timeouts based on model characteristics."""

    BASE_SECONDS: int = 20
    PER_GB_SECONDS: int = 2

    @staticmethod
    def timeout_for_model(model_size_gb: int) -> int:
        if model_size_gb < 0:
            raise ValueError("Model size cannot be negative")
        return HealthCheckTimeoutCalculator.BASE_SECONDS + (
            model_size_gb // HealthCheckTimeoutCalculator.PER_GB_SECONDS
        )

    @staticmethod
    def max_retries(
        timeout_seconds: int,
        interval_seconds: int = 5,
    ) -> int:
        if timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        if interval_seconds <= 0:
            raise ValueError("Interval must be positive")
        return timeout_seconds // interval_seconds
