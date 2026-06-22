"""Inbound port - stop services."""

from typing import Protocol

from ...dtos.requests.stop_services_request import StopServicesRequest
from ...dtos.responses.stop_services_response import StopServicesResponse


class StopServicesPort(Protocol):
    """Port for stopping services."""

    def execute(self, request: StopServicesRequest) -> StopServicesResponse:
        ...
