"""Request DTO for listing services."""


class ListServicesRequest:
    """Request to list running services."""

    def __init__(self, compose_file: str) -> None:
        self.compose_file = compose_file
