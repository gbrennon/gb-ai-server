"""Request DTO for showing service logs."""


class ShowLogsRequest:
    """Request to show service logs."""

    def __init__(
        self,
        compose_file: str,
        service: str | None = None,
        follow: bool = False,
    ) -> None:
        self.compose_file = compose_file
        self.service = service
        self.follow = follow
