"""Service implementation for showing logs."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ComposeTool
from ..dtos.requests.show_logs_request import ShowLogsRequest
from ..dtos.responses.show_logs_response import ShowLogsResponse


class ShowLogsService:
    """Show service logs using compose tool."""

    def __init__(self, logger: Logger, compose_tool: ComposeTool) -> None:
        self.logger = logger
        self.compose_tool = compose_tool

    def execute(self, request: ShowLogsRequest) -> ShowLogsResponse:
        result = self.compose_tool.logs(
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
