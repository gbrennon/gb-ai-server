"""Model entry domain logic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelEntry:
    """
    Immutable model specification entry.

    Holds only what is needed to identify and download the model.
    Context window is NOT stored here — it is derived at runtime from the
    HuggingFace Hub library (config.json) by fetch_safe_ctx_size().

    Supports two parse formats for backward compatibility:
      3-part: "display_name|filename|download_url"
      5-part: "display_name|filename|download_url|n_gpu_layers|ctx_size"
              (ctx_size field is accepted but ignored — HF is the source of truth)
    """

    display_name: str
    filename: str
    url: str
    n_gpu_layers: int = 999

    @classmethod
    def from_string(cls, entry: str) -> ModelEntry:
        """
        Parse model entry from pipe-delimited string.

        Args:
            entry: "display_name|filename|url"
                or "display_name|filename|url|n_gpu_layers|ctx_size"
                (ctx_size accepted for compatibility but not stored)

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
        if len(parts) == 5:
            n_gpu_layers = int(parts[3].strip())
            # parts[4] is ctx_size — ignored, HF lib is the source of truth

        return cls(
            display_name=display_name.strip(),
            filename=filename.strip(),
            url=url.strip(),
            n_gpu_layers=n_gpu_layers,
        )

    @classmethod
    def from_tuple(cls, entry: tuple) -> ModelEntry:
        """
        Create ModelEntry from tuple.

        Args:
            entry: (display_name, filename, url)
                or (display_name, filename, url, n_gpu_layers, ctx_size)
                (ctx_size accepted for compatibility but not stored)

        Returns:
            ModelEntry instance.
        """
        n_gpu_layers = entry[3] if len(entry) >= 4 else 999
        # entry[4] would be ctx_size — ignored, HF lib is the source of truth
        return cls(
            display_name=entry[0],
            filename=entry[1],
            url=entry[2],
            n_gpu_layers=n_gpu_layers,
        )

    def __str__(self) -> str:
        """Serialize to pipe-delimited format."""
        return f"{self.display_name}|{self.filename}|{self.url}"
