"""Request DTO for registering a model with agentic tools."""


class RegisterModelsRequest:
    """Request to register a single model with a coding assistant."""

    def __init__(
        self,
        model: tuple[str, str, int, str],
        provider_base_url: str | None = None,
    ) -> None:
        """
        Args:
            model: Tuple of (display_name, filename, port, container_name)
            provider_base_url: Optional base URL override
        """
        self.model = model
        self.provider_base_url = provider_base_url
