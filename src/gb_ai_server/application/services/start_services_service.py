"""Service implementation for starting services."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeTool
from ..dtos.requests.start_services_request import StartServicesRequest
from ..dtos.responses.start_services_response import StartServicesResponse


class StartServicesService:
    """Start services using compose tool."""

    def __init__(self, logger: Logger, compose_tool: ComposeTool) -> None:
        self.logger = logger
        self.compose_tool = compose_tool

    def execute(self, request: StartServicesRequest) -> StartServicesResponse:
        self.logger.section("Starting Services")
        result = self.compose_tool.up(
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
