"""Response DTO for restarting services."""


class RestartServicesResponse:
    """Result of restarting services."""

    def __init__(self, success: bool) -> None:
        self.success = success
