"""Inbound port - restart services."""

from typing import Protocol

from ...dtos.requests.restart_services_request import RestartServicesRequest
from ...dtos.responses.restart_services_response import RestartServicesResponse


class RestartServicesPort(Protocol):
    """Port for restarting services."""

    def execute(self, request: RestartServicesRequest) -> RestartServicesResponse:
        ...
