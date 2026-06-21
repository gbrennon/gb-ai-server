"""Model file copying to containers service."""

from pathlib import Path
from typing import Sequence

from ..core import Logger
from ..domain import ModelEntry
from ..infrastructure import ContainerRuntime


class ModelCopier:
    """Copy model files into running containers."""

    def __init__(self, logger: Logger, container_runtime: ContainerRuntime) -> None:
        """
        Initialize model copier.

        Args:
            logger: Logger instance.
            container_runtime: Container runtime to use.
        """
        self.logger = logger
        self.runtime = container_runtime

    def copy_models(
        self,
        entries: Sequence[ModelEntry],
        source_dir: Path,
        container_name: str,
        dest_dir: str = "/models",
    ) -> dict[str, bool]:
        """
        Copy multiple models to container.

        Args:
            entries: Model entries to copy.
            source_dir: Source directory containing models.
            container_name: Target container name.
            dest_dir: Destination directory in container.

        Returns:
            Dict mapping model display name to copy success.
        """
        if not self.runtime.is_running(container_name):
            self.logger.warn(
                f"Container {container_name} not running, skipping copy"
            )
            return {entry.display_name: False for entry in entries}

        self.logger.section("Copying Models to Container")

        results: dict[str, bool] = {}
        for entry in entries:
            results[entry.display_name] = self.copy_model(
                entry,
                source_dir,
                container_name,
                dest_dir,
            )

        return results

    def copy_model(
        self,
        entry: ModelEntry,
        source_dir: Path,
        container_name: str,
        dest_dir: str = "/models",
    ) -> bool:
        """
        Copy single model to container.

        Args:
            entry: Model entry.
            source_dir: Source directory.
            container_name: Target container name.
            dest_dir: Destination directory in container.

        Returns:
            True if successful.
        """
        source = source_dir / entry.filename

        if not source.exists():
            self.logger.warn(
                f"{entry.display_name} not found at {source}, skipping"
            )
            return False

        self.logger.info(f"Copying {entry.display_name} to {container_name}...")

        result = self.runtime.copy_to(
            source,
            container_name,
            f"{dest_dir}/{entry.filename}",
        )

        if result.success:
            self.logger.ok(f"Copied {entry.display_name}")
            return True
        else:
            self.logger.warn(f"Failed to copy {entry.display_name}")
            if result.stderr:
                self.logger.debug(result.stderr)
            return False
