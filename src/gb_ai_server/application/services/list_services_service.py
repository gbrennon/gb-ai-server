"""Service implementation for listing services."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeQuery
from ..dtos.requests.list_services_request import ListServicesRequest
from ..dtos.responses.list_services_response import ListServicesResponse
from ..utils import print_section


class ListServicesService:
    """List running services using compose tool."""

    def __init__(self, logger: Logger, compose_query: ComposeQuery | None = None) -> None:
        self.logger = logger
        self.compose_query = compose_query

    def execute(self, request: ListServicesRequest) -> ListServicesResponse:
        if not self.compose_query:
            self.logger.error("Compose query tool is not available. Cannot list services.")
            return ListServicesResponse(False)

        print_section("Service Status")
        result = self.compose_query.ps(Path(request.compose_file))
        if result.success:
            output = result.stdout
            print(output)
            return ListServicesResponse(True, output)
        else:
            self.logger.warn("No services running")
            return ListServicesResponse(False)
