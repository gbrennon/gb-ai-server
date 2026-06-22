"""Inbound port - download models."""

from typing import Protocol

from ...dtos.requests.download_models_request import DownloadModelsRequest
from ...dtos.responses.download_models_response import DownloadModelsResponse


class DownloadModelsPort(Protocol):
    """Port for downloading model files."""

    def execute(self, request: DownloadModelsRequest) -> DownloadModelsResponse:
        ...
