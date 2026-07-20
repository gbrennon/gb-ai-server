"""Model entry domain logic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelEntry:
    """
    Immutable model specification entry.

    Holds only what is needed to identify and download the model.
    Context window and GPU layers are NOT stored here — they are derived
    at runtime from the HuggingFace Hub library (config.json) and
    available VRAM via GPULayerCalculator.

    Supports two parse formats for backward compatibility:
      3-part: "display_name|filename|download_url"
      5-part: "display_name|filename|download_url|n_gpu_layers|ctx_size"
              (both n_gpu_layers and ctx_size are accepted but ignored —
               HF config + VRAM probe are the source of truth at runtime)
    """

    display_name: str
    filename: str
    url: str

    @classmethod
    def from_string(cls, entry: str) -> ModelEntry:
        """
        Parse model entry from pipe-delimited string.

        Args:
            entry: "display_name|filename|url"
                or "display_name|filename|url|n_gpu_layers|ctx_size"
                (n_gpu_layers and ctx_size accepted for compatibility
                 but not stored — calculated at runtime)

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

        # parts[3] (n_gpu_layers) and parts[4] (ctx_size) are ignored —
        # both are calculated at runtime from HF config + VRAM probe.

        return cls(
            display_name=display_name.strip(),
            filename=filename.strip(),
            url=url.strip(),
        )

    @classmethod
    def from_tuple(cls, entry: tuple) -> ModelEntry:
        """
        Create ModelEntry from tuple.

        Args:
            entry: (display_name, filename, url)
                or (display_name, filename, url, n_gpu_layers, ctx_size)
                (n_gpu_layers and ctx_size accepted for compatibility
                 but not stored — calculated at runtime)

        Returns:
            ModelEntry instance.
        """
        # entry[3] (n_gpu_layers) and entry[4] (ctx_size) are ignored —
        # both are calculated at runtime from HF config + VRAM probe.
        return cls(
            display_name=entry[0],
            filename=entry[1],
            url=entry[2],
        )

    def __str__(self) -> str:
        """Serialize to pipe-delimited format."""
        return f"{self.display_name}|{self.filename}|{self.url}"
