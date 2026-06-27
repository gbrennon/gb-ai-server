"""Model entry domain logic."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelEntry:
    """
    Immutable model specification entry.

    Supports two formats:
      3-part: "display_name|filename|download_url"
      5-part: "display_name|filename|download_url|n_gpu_layers|ctx_size"

    ctx_size defaults to the CTX_SIZE environment variable if set,
    otherwise 8192. The 5-part string/tuple format always overrides.
    """

    display_name: str
    filename: str
    url: str
    n_gpu_layers: int = 999
    ctx_size: int = field(default_factory=lambda: ModelEntry._resolve_default_ctx_size())  # type: ignore[arg-type]

    @staticmethod
    def _resolve_default_ctx_size() -> int:
        """Resolve the default context size from CTX_SIZE env var, or 8192."""
        raw = os.environ.get("CTX_SIZE")
        if raw is not None:
            try:
                return int(raw.strip())
            except (ValueError, TypeError):
                pass
        return 8192

    @classmethod
    def from_string(cls, entry: str) -> ModelEntry:
        """
        Parse model entry from pipe-delimited string.

        Args:
            entry: String in 3-part "display_name|filename|url"
                    or 5-part "display_name|filename|url|n_gpu_layers|ctx_size"

        Returns:
            ModelEntry instance.

        Raises:
            ValueError: If entry format is invalid.
        """
        parts = entry.split("|")
        if len(parts) not in (3, 5):
            msg = (
                f"Invalid model entry format: {entry}. "
                "Expected: display_name|filename|url "
                "or display_name|filename|url|n_gpu_layers|ctx_size"
            )
            raise ValueError(msg)

        display_name, filename, url = parts[0], parts[1], parts[2]
        if not all([display_name, filename, url]):
            raise ValueError("Model entry contains empty fields")

        n_gpu_layers = 999
        ctx_size = cls._resolve_default_ctx_size()
        if len(parts) == 5:
            n_gpu_layers = int(parts[3].strip())
            ctx_size = int(parts[4].strip())

        return cls(
            display_name=display_name.strip(),
            filename=filename.strip(),
            url=url.strip(),
            n_gpu_layers=n_gpu_layers,
            ctx_size=ctx_size,
        )

    @classmethod
    def from_tuple(cls, entry: tuple) -> ModelEntry:
        """
        Create ModelEntry from tuple.

        Args:
            entry: Tuple of (display_name, filename, url)
                    or (display_name, filename, url, n_gpu_layers, ctx_size)

        Returns:
            ModelEntry instance.
        """
        if len(entry) == 5:
            return cls(
                display_name=entry[0],
                filename=entry[1],
                url=entry[2],
                n_gpu_layers=entry[3],
                ctx_size=entry[4],
            )
        return cls(
            display_name=entry[0],
            filename=entry[1],
            url=entry[2],
        )

    def __str__(self) -> str:
        """Serialize to pipe-delimited format."""
        return f"{self.display_name}|{self.filename}|{self.url}"
