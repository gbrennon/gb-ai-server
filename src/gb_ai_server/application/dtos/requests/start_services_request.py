"""Request DTO for starting services."""


class StartServicesRequest:
    """Request to start services."""

    def __init__(
        self,
        compose_file: str,
        services: tuple[str, ...] = (),
    ) -> None:
        self.compose_file = compose_file
        self.services = services
