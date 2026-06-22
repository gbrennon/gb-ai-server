"""Request DTO for stopping services."""


class StopServicesRequest:
    """Request to stop all services."""

    def __init__(self, compose_file: str) -> None:
        self.compose_file = compose_file
