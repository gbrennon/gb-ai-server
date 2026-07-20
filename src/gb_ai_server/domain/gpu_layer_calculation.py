"""Result of GPU layer calculation for a model on specific hardware."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GPULayerCalculation:
    """Immutable result of computing how many transformer layers fit in GPU VRAM.

    Produced by GPULayerCalculator from ModelMetadata + available VRAM.
    """

    total_layers: int
    gpu_layers: int
    cpu_layers: int
    model_memory_mb: float
    available_vram_mb: float
    per_layer_memory_mb: float

    @property
    def is_fully_offloaded(self) -> bool:
        """True when all layers fit on GPU."""
        return self.gpu_layers >= self.total_layers

    @property
    def is_cpu_only(self) -> bool:
        """True when no layers fit on GPU."""
        return self.gpu_layers == 0
