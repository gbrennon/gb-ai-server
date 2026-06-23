"""Service implementation for registering models with agentic tools."""

from ..ports.outbound.logger import Logger
from ..ports.outbound import ModelRegistrar
from ..dtos.requests.register_models_request import RegisterModelsRequest
from ..dtos.responses.register_models_response import RegisterModelsResponse


class RegisterModelsService:
    """Register local models with agentic coding assistants."""

    def __init__(self, logger: Logger, registrar: ModelRegistrar) -> None:
        self.logger = logger
        self.registrar = registrar

    def execute(self, request: RegisterModelsRequest) -> RegisterModelsResponse:
        if not request.models:
            self.logger.warn("No models provided for registration")
            return RegisterModelsResponse(success=False, registered_models=[])

        self.logger.info(
            f"Registering {len(request.models)} model(s) with agentic tool..."
        )

        success = self.registrar.register_models(
            models=request.models,
            provider_base_url=request.provider_base_url,
        )

        registered_models = [name for name, _, _, _ in request.models]
        return RegisterModelsResponse(
            success=success,
            registered_models=registered_models,
        )
