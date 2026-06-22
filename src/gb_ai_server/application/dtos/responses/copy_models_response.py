"""Response DTO for copying models."""


class CopyModelsResponse:
    """Result of copying models to container."""

    def __init__(self, results: dict[str, bool]) -> None:
        self.results = results
