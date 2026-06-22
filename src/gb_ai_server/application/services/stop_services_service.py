"""Service implementation for stopping services."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeTool
from ..dtos.requests.stop_services_request import StopServicesRequest
from ..dtos.responses.stop_services_response import StopServicesResponse


class StopServicesService:
    """Stop services using compose tool."""

    def __init__(self, logger: Logger, compose_tool: ComposeTool) -> None:
        self.logger = logger
        self.compose_tool = compose_tool

    def execute(self, request: StopServicesRequest) -> StopServicesResponse:
        self.logger.section("Stopping Services")
        result = self.compose_tool.down(Path(request.compose_file))
        if result.success:
            self.logger.ok("Services stopped")
            return StopServicesResponse(True)
        else:
            self.logger.warn("Failed to stop services gracefully")
            return StopServicesResponse(False)
