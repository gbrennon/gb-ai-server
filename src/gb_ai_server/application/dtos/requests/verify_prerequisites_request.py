"""Request DTO for verifying prerequisites."""


class VerifyPrerequisitesRequest:
    """Request to verify system prerequisites."""

    def __init__(self, compose_file: str) -> None:
        self.compose_file = compose_file
