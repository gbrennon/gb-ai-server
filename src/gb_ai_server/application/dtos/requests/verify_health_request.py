"""Request DTO for health verification."""


class VerifyHealthRequest:
    """Request to verify service health."""

    def __init__(
        self,
        ports: tuple[int, ...],
        timeout_seconds: int = 60,
        interval_seconds: int = 5,
    ) -> None:
        self.ports = ports
        self.timeout_seconds = timeout_seconds
        self.interval_seconds = interval_seconds
