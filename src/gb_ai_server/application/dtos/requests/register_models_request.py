"""Request DTO for registering models with agentic tools."""


class RegisterModelsRequest:
    """Request to register models with a coding assistant."""

    def __init__(
        self,
        models: list[tuple[str, str, int]],
        provider_base_url: str | None = None,
    ) -> None:
        self.models = models
        self.provider_base_url = provider_base_url
