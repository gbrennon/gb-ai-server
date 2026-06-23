"""Request DTO for registering models with agentic tools."""


class RegisterModelsRequest:
    """Request to register models with a coding assistant."""

    def __init__(
        self,
        models: list[tuple[str, str, int, str]],
        provider_base_url: str | None = None,
    ) -> None:
        """
        Args:
            models: List of tuples (display_name, filename, port, container_name)
            provider_base_url: Optional base URL override
        """
        self.models = models
        self.provider_base_url = provider_base_url
