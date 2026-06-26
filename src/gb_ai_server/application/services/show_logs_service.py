"""Service implementation for showing logs."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeQuery
from ..dtos.requests.show_logs_request import ShowLogsRequest
from ..dtos.responses.show_logs_response import ShowLogsResponse


class ShowLogsService:
    """Show service logs using compose tool."""

    def __init__(self, logger: Logger, compose_query: ComposeQuery | None = None) -> None:
        self.logger = logger
        self.compose_query = compose_query

    def execute(self, request: ShowLogsRequest) -> ShowLogsResponse:
        if not self.compose_query:
            self.logger.error("Compose query tool is not available. Cannot retrieve logs.")
            return ShowLogsResponse(False)

        result = self.compose_query.logs(
            Path(request.compose_file),
            service=request.service,
            follow=request.follow,
        )
        if result.success:
            output = result.stdout
            if output:
                print(output)
            return ShowLogsResponse(True, output)
        else:
            self.logger.error("Failed to retrieve logs")
            return ShowLogsResponse(False)
