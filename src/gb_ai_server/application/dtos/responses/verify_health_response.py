"""Response DTO for health verification."""


class VerifyHealthResponse:
    """Result of health verification."""

    def __init__(self, success: bool) -> None:
        self.success = success
