"""Inbound port - start services."""

from typing import Protocol

from ...dtos.requests.start_services_request import StartServicesRequest
from ...dtos.responses.start_services_response import StartServicesResponse


class StartServicesPort(Protocol):
    """Port for starting services."""

    def execute(self, request: StartServicesRequest) -> StartServicesResponse:
        ...
