"""Service implementation for listing services."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeTool
from ..dtos.requests.list_services_request import ListServicesRequest
from ..dtos.responses.list_services_response import ListServicesResponse


class ListServicesService:
    """List running services using compose tool."""

    def __init__(self, logger: Logger, compose_tool: ComposeTool) -> None:
        self.logger = logger
        self.compose_tool = compose_tool

    def execute(self, request: ListServicesRequest) -> ListServicesResponse:
        self.logger.section("Service Status")
        result = self.compose_tool.ps(Path(request.compose_file))
        if result.success:
            output = result.stdout
            print(output)
            return ListServicesResponse(True, output)
        else:
            self.logger.warn("No services running")
            return ListServicesResponse(False)
