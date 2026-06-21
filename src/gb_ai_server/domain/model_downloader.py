"""Domain layer - model downloader protocol."""

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
        """
        Download a model file.

        Args:
            model_name: Human-readable model name.
            filename: Target filename.
            url: Download URL (HuggingFace or direct).
            destination: Destination directory.
            token: Optional HuggingFace token for gated repos.

        Returns:
            True if download succeeded, False otherwise.
        """
        ...

    def exists(self, filename: str, destination: Path) -> bool:
        """
        Check if model file already exists.

        Args:
            filename: Filename to check.
            destination: Directory to check in.

        Returns:
            True if file exists and has non-zero size.
        """
        ...