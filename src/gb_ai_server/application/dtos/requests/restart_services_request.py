"""Request DTO for restarting services."""


class RestartServicesRequest:
    """Request to restart services."""

    def __init__(
        self,
        compose_file: str,
        services: tuple[str, ...] = (),
    ) -> None:
        self.compose_file = compose_file
        self.services = services
