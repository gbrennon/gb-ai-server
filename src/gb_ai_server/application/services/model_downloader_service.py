"""Service implementation for downloading models."""

from pathlib import Path

from ..ports.outbound.logger import Logger
from ..ports.outbound import ModelDownloader
from ..dtos.requests.download_models_request import DownloadModelsRequest
from ..dtos.responses.download_models_response import DownloadModelsResponse


class ModelDownloaderService:
    """Orchestrate model downloads using a ModelDownloader implementation."""

    def __init__(self, logger: Logger, downloader: ModelDownloader) -> None:
        self.logger = logger
        self.downloader = downloader

    def execute(self, request: DownloadModelsRequest) -> DownloadModelsResponse:
        destination = Path(request.destination_dir)
        destination.mkdir(parents=True, exist_ok=True)
        results: dict[str, bool] = {}

        for display_name, filename, url in request.entries:
            results[display_name] = self.downloader.download(
                display_name,
                filename,
                url,
                destination,
                token=request.token,
            )

        return DownloadModelsResponse(results)
