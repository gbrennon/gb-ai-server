"""Inbound port - copy models."""

from typing import Protocol

from ...dtos.requests.copy_models_request import CopyModelsRequest
from ...dtos.responses.copy_models_response import CopyModelsResponse


class CopyModelsPort(Protocol):
    """Port for copying model files to containers."""

    def execute(self, request: CopyModelsRequest) -> CopyModelsResponse:
        ...
