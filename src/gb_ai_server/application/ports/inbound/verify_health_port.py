"""Inbound port - verify health."""

from typing import Protocol

from ...dtos.requests.verify_health_request import VerifyHealthRequest
from ...dtos.responses.verify_health_response import VerifyHealthResponse


class VerifyHealthPort(Protocol):
    """Port for verifying service health."""

    def execute(self, request: VerifyHealthRequest) -> VerifyHealthResponse:
        ...
