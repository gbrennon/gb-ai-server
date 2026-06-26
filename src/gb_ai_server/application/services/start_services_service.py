"""Service implementation for starting services."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeLifecycle
from ..dtos.requests.start_services_request import StartServicesRequest
from ..dtos.responses.start_services_response import StartServicesResponse
from ..utils import print_section


class StartServicesService:
    """Start services using compose tool."""

    def __init__(self, logger: Logger, compose_lifecycle: ComposeLifecycle | None = None) -> None:
        self.logger = logger
        self.compose_lifecycle = compose_lifecycle

    def execute(self, request: StartServicesRequest) -> StartServicesResponse:
        if not self.compose_lifecycle:
            self.logger.error("Compose lifecycle operator is not available. Cannot start services.")
            return StartServicesResponse(False)

        print_section("Starting Services")
        result = self.compose_lifecycle.up(
            Path(request.compose_file),
            *request.services,
            detach=True,
        )
        if result.success:
            self.logger.ok("Services started")
            return StartServicesResponse(True)
        else:
            self.logger.error("Failed to start services")
            if result.stderr:
                self.logger.debug(result.stderr)
            return StartServicesResponse(False)
