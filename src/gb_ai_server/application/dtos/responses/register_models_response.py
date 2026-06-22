"""Response DTO for registering models."""


class RegisterModelsResponse:
    """Result of model registration operation."""

    def __init__(self, success: bool, registered_models: list[str]) -> None:
        self.success = success
        self.registered_models = registered_models
