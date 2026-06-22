"""Inbound port - show logs."""

from typing import Protocol

from ...dtos.requests.show_logs_request import ShowLogsRequest
from ...dtos.responses.show_logs_response import ShowLogsResponse


class ShowLogsPort(Protocol):
    """Port for showing service logs."""

    def execute(self, request: ShowLogsRequest) -> ShowLogsResponse:
        ...
