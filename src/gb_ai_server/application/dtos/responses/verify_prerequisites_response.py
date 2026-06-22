"""Response DTO for prerequisite verification."""


class VerifyPrerequisitesResponse:
    """Result of prerequisite verification."""

    def __init__(self, success: bool) -> None:
        self.success = success
