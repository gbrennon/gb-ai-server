"""Inbound port - verify prerequisites."""

from typing import Protocol

from ...dtos.requests.verify_prerequisites_request import VerifyPrerequisitesRequest
from ...dtos.responses.verify_prerequisites_response import VerifyPrerequisitesResponse


class VerifyPrerequisitesPort(Protocol):
    """Port for verifying system prerequisites."""

    def execute(self, request: VerifyPrerequisitesRequest) -> VerifyPrerequisitesResponse:
        ...
