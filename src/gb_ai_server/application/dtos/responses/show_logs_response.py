"""Response DTO for showing logs."""


class ShowLogsResponse:
    """Result of showing service logs."""

    def __init__(self, success: bool, output: str | None = None) -> None:
        self.success = success
        self.output = output
