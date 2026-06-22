"""Outbound port - model downloader interface."""

from pathlib import Path
from typing import Protocol


class ModelDownloader(Protocol):
    """Protocol for model downloaders."""

    def download(
        self,
        model_name: str,
        filename: str,
        url: str,
        destination: Path,
        token: str | None = None,
    ) -> bool:
        ...

    def exists(self, filename: str, destination: Path) -> bool:
        ...
