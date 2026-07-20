"""Model architecture metadata extracted from HuggingFace config.json."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelMetadata:
    """Immutable snapshot of model architecture parameters.

    Extracted from HuggingFace config.json. Used by GPULayerCalculator
    to determine how many transformer layers fit on the GPU.
    """

    num_hidden_layers: int
    hidden_size: int
    num_kv_heads: int
    head_dim: int
    vocab_size: int
    max_position_embeddings: int
    repo_id: str = ""

    @property
    def native_context_window(self) -> int:
        """The model's native maximum context window in tokens."""
        return self.max_position_embeddings
