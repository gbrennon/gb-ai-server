"""Inbound port - list services."""

from typing import Protocol

from ...dtos.requests.list_services_request import ListServicesRequest
from ...dtos.responses.list_services_response import ListServicesResponse


class ListServicesPort(Protocol):
    """Port for listing running services."""

    def execute(self, request: ListServicesRequest) -> ListServicesResponse:
        ...
