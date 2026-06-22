"""Request DTO for downloading models."""


class DownloadModelsRequest:
    """Request to download multiple models."""

    def __init__(
        self,
        entries: list[tuple[str, str, str]],
        destination_dir: str,
        skip_existing: bool = True,
        token: str | None = None,
    ) -> None:
        self.entries = entries
        self.destination_dir = destination_dir
        self.skip_existing = skip_existing
        self.token = token
