"""Response DTO for downloading models."""


class DownloadModelsResponse:
    """Result of model download operation."""

    def __init__(self, results: dict[str, bool]) -> None:
        self.results = results
