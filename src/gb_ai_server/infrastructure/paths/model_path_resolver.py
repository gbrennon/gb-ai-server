"""Multi-directory model path resolution."""

from pathlib import Path


class ModelPathResolver:
    """Search multiple model directories for model files.

    Directories are searched in order. The first directory is
    the primary (writable) directory where new downloads go.
    Subsequent directories are read-only fallback locations
    (e.g., USB drives or network mounts).
    """

    def __init__(self, dirs: list[Path]) -> None:
        if not dirs:
            raise ValueError("At least one model directory is required")
        self._dirs = dirs

    def primary(self) -> Path:
        """Return the first (writable) directory for downloads."""
        return self._dirs[0]

    def resolve(self, filename: str) -> Path | None:
        """Return the first existing path for *filename*, or None.

        A file is considered existing if it is present and has
        a size greater than zero.
        """
        for d in self._dirs:
            path = d / filename
            if path.exists() and path.stat().st_size > 0:
                return path
        return None

    def all_dirs(self) -> list[Path]:
        """Return a copy of all directories."""
        return list(self._dirs)
