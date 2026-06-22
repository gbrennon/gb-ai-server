"""Response DTO for listing services."""


class ListServicesResponse:
    """Result of listing services."""

    def __init__(self, success: bool, output: str | None = None) -> None:
        self.success = success
        self.output = output
