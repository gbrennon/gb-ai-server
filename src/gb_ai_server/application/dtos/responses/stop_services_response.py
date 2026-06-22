"""Response DTO for stopping services."""


class StopServicesResponse:
    """Result of stopping services."""

    def __init__(self, success: bool) -> None:
        self.success = success
