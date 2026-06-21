"""Infrastructure layer - model downloader implementation using huggingface_hub."""

import os
from pathlib import Path
from typing import Optional

from ..core import Logger
from ..domain import ModelDownloader as ModelDownloaderProtocol


class HuggingFaceModelDownloader:
    """Download models from Hugging Face Hub using huggingface_hub library."""

    def __init__(self, logger: Logger) -> None:
        """
        Initialize downloader.

        Args:
            logger: Logger instance.
        """
        self.logger = logger

    def download(
        self,
        model_name: str,
        filename: str,
        url: str,
        destination: Path,
        token: Optional[str] = None,
    ) -> bool:
        """
        Download a model file from Hugging Face Hub.

        Args:
            model_name: Human-readable model name.
            filename: Target filename.
            url: Download URL (Hugging Face resolve URL).
            destination: Destination directory.
            token: Optional HuggingFace token for gated repos.

        Returns:
            True if download succeeded, False otherwise.
        """
        destination.mkdir(parents=True, exist_ok=True)
        dest_path = destination / filename

        if self.exists(filename, destination):
            self.logger.info(f"{model_name} already exists: {dest_path}")
            return True

        self.logger.info(f"Downloading {model_name} from {url}...")

        try:
            from huggingface_hub import hf_hub_download

            repo_id, file_path = self._parse_hf_url(url)
            if not repo_id:
                self.logger.warn(f"Could not parse HF repo from URL: {url}")
                return False

            hf_token = token or os.getenv("HF_TOKEN")

            hf_hub_download(
                repo_id=repo_id,
                filename=file_path,
                local_dir=destination,
                local_dir_use_symlinks=False,
                token=hf_token,
            )

            if dest_path.exists() and dest_path.stat().st_size > 0:
                size_mb = dest_path.stat().st_size / (1024 * 1024)
                self.logger.ok(f"Downloaded {model_name} ({size_mb:.1f}MB)")
                return True
            else:
                self.logger.warn(f"Download completed but file not found: {dest_path}")
                return False

        except ImportError:
            self.logger.warn("huggingface_hub not installed, falling back to curl")
            return self._download_with_curl(model_name, url, dest_path)
        except Exception as e:
            self.logger.warn(f"Failed to download {model_name}: {e}")
            return False

    def exists(self, filename: str, destination: Path) -> bool:
        """
        Check if model file already exists.

        Args:
            filename: Filename to check.
            destination: Directory to check in.

        Returns:
            True if file exists and has non-zero size.
        """
        path = destination / filename
        return path.exists() and path.stat().st_size > 0

    def _parse_hf_url(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse Hugging Face URL to extract repo_id and file_path.

        Expected format: https://huggingface.co/{repo_id}/resolve/main/{file_path}

        Returns:
            Tuple of (repo_id, file_path) or (None, None) if parsing fails.
        """
        import re

        patterns = [
            r"huggingface\.co/([^/]+/[^/]+)/resolve/main/(.+)",
            r"huggingface\.co/([^/]+/[^/]+)/resolve/[^/]+/(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)

        return None, None

    def _download_with_curl(
        self, model_name: str, url: str, dest_path: Path
    ) -> bool:
        """Fallback download using curl."""
        from ..core import Command

        result = Command.run(
            "curl",
            "-L",
            "-o",
            str(dest_path),
            url,
            capture_output=True,
        )

        if result.success and dest_path.exists() and dest_path.stat().st_size > 0:
            size_mb = dest_path.stat().st_size / (1024 * 1024)
            self.logger.ok(f"Downloaded {model_name} ({size_mb:.1f}MB)")
            return True
        else:
            self.logger.warn(f"Failed to download {model_name}")
            if result.stderr:
                self.logger.debug(f"Error: {result.stderr}")
            return False