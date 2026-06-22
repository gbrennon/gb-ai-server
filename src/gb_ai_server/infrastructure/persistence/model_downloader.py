"""Infrastructure layer - model downloader implementation using huggingface_hub."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...application.ports.outbound.logger import Logger


class HuggingFaceModelDownloader:
    """Download models from Hugging Face Hub using huggingface_hub library."""

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def download(
        self,
        model_name: str,
        filename: str,
        url: str,
        destination: Path,
        token: str | None = None,
    ) -> bool:
        destination.mkdir(parents=True, exist_ok=True)
        dest_path = destination / filename

        if self.exists(filename, destination):
            self.logger.info(f"{model_name} already exists: {dest_path}")
            return True

        self.logger.info(f"Downloading {model_name} from {url}...")

        try:
            from huggingface_hub import hf_hub_download

            repo_id, file_path = self._parse_hf_url(url)
            if not repo_id or not file_path:
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
        path = destination / filename
        return path.exists() and path.stat().st_size > 0

    def _parse_hf_url(self, url: str) -> tuple[str | None, str | None]:
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
        from ..command import Command

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
