"""Model download orchestration service."""

from pathlib import Path
from typing import Sequence

from ..core import Logger
from ..domain import ModelEntry, ModelDownloader


class ModelDownloadService:
    """Orchestrate model downloads using a ModelDownloader implementation."""

    def __init__(self, logger: Logger, downloader: ModelDownloader) -> None:
        """
        Initialize service.

        Args:
            logger: Logger instance.
            downloader: ModelDownloader implementation (from infrastructure).
        """
        self.logger = logger
        self.downloader = downloader

    def download_models(
        self,
        entries: Sequence[ModelEntry],
        destination_dir: Path,
        skip_existing: bool = True,
        token: str | None = None,
    ) -> dict[str, bool]:
        """
        Download multiple models.

        Args:
            entries: Model entries to download.
            destination_dir: Directory to save models.
            skip_existing: Skip if file already exists.
            token: Optional HuggingFace token for gated repos.

        Returns:
            Dict mapping model display name to download success.
        """
        destination_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, bool] = {}

        for entry in entries:
            results[entry.display_name] = self.downloader.download(
                entry.display_name,
                entry.filename,
                entry.url,
                destination_dir,
                token=token,
            )

        return results