"""Response DTO for starting services."""


class StartServicesResponse:
    """Result of starting services."""

    def __init__(self, success: bool) -> None:
        self.success = success
