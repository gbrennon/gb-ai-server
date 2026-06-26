"""Service implementation for registering a model with agentic tools."""

from ..ports.outbound.logger import Logger
from ..ports.outbound import ModelRegistrar
from ..dtos.requests.register_models_request import RegisterModelsRequest
from ..dtos.responses.register_models_response import RegisterModelsResponse


class RegisterModelsService:
    """Register a local model with agentic coding assistants."""

    def __init__(self, logger: Logger, registrar: ModelRegistrar) -> None:
        self.logger = logger
        self.registrar = registrar

    def execute(self, request: RegisterModelsRequest) -> RegisterModelsResponse:
        if request.model is None:
            self.logger.warn("No model provided for registration")
            return RegisterModelsResponse(success=False, registered_models=[])

        self.logger.info(
            f"Registering model with agentic tool..."
        )

        success = self.registrar.register_model(
            model=request.model,
            provider_base_url=request.provider_base_url,
        )

        registered_models = [request.model[0]]
        return RegisterModelsResponse(
            success=success,
            registered_models=registered_models,
        )
