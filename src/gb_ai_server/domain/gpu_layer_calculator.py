"""Calculate how many transformer layers fit on GPU given available VRAM.

Pure domain logic — no I/O, no hardware probing. Takes ModelMetadata and
available VRAM as inputs; returns a GPULayerCalculation.
"""

from __future__ import annotations

from .model_metadata import ModelMetadata
from .gpu_layer_calculation import GPULayerCalculation


class GPULayerCalculator:
    """Calculates GPU layer offloading from model architecture and available VRAM.

    Agnostic to specific hardware — uses available VRAM as input.
    Uses a simplified parameter-counting formula based on hidden_size,
    num_hidden_layers, and vocab_size. The approximation accounts for
    attention (Q/K/V/O projections) and feed-forward network weights.

    Actual GGUF quantized models are typically 4-8× smaller than the
    float32 parameter count, but the overhead multiplier accounts for
    activations, KV cache, and CUDA runtime overhead, giving a
    conservative estimate that errs on the side of fitting.
    """

    # Bytes per parameter (4 bytes for float32)
    BYTES_PER_PARAM: int = 4

    # Overhead multiplier for activations and intermediate computations.
    # 2.5× the model size for inference is a typical estimate accounting
    # for KV cache, attention activations, and CUDA runtime overhead.
    ACTIVATION_OVERHEAD: float = 2.5

    # Reserve 20% of VRAM for CUDA runtime, scratch buffers, and safety margin
    VRAM_SAFETY_FACTOR: float = 0.8

    def __init__(self, metadata: ModelMetadata) -> None:
        """Initialize calculator for a specific model's architecture.

        Args:
            metadata: Model architecture parameters from HuggingFace config.json.
        """
        self.metadata = metadata

    def calculate_total_model_memory(self) -> float:
        """Estimate total model memory including weights and activations.

        Uses a simplified formula based on hidden_size, num_hidden_layers,
        and vocab_size. Per-layer parameters approximate attention (Q/K/V/O)
        plus feed-forward network weights.

        Returns:
            float: Estimated memory in MB.
        """
        # Embedding layer: vocab_size × hidden_size
        embedding_params = self.metadata.vocab_size * self.metadata.hidden_size

        # Per transformer layer ≈ 12 × hidden_size²
        # (4 projections in attention + 8 in feed-forward ≈ 12)
        layer_params = 12 * (self.metadata.hidden_size ** 2)
        total_layer_params = layer_params * self.metadata.num_hidden_layers

        total_params = embedding_params + total_layer_params

        model_size_mb = (total_params * self.BYTES_PER_PARAM) / (1024 ** 2)
        return model_size_mb * self.ACTIVATION_OVERHEAD

    def calculate_per_layer_memory(self) -> float:
        """Estimate memory required per transformer layer.

        Returns:
            float: Memory in MB per layer (including activation overhead).
        """
        params_per_layer = 12 * (self.metadata.hidden_size ** 2)
        layer_memory_mb = (params_per_layer * self.BYTES_PER_PARAM) / (1024 ** 2)
        return layer_memory_mb * self.ACTIVATION_OVERHEAD

    def calculate_gpu_layers(self, available_vram_mb: float) -> GPULayerCalculation:
        """Calculate how many layers fit on GPU.

        Args:
            available_vram_mb: Available GPU VRAM in MB (free or total).

        Returns:
            GPULayerCalculation with layer split, memory estimates, and VRAM info.

        Raises:
            ValueError: If VRAM is zero or negative.
        """
        if available_vram_mb <= 0:
            raise ValueError("Available VRAM must be greater than 0")

        per_layer_mb = self.calculate_per_layer_memory()

        if per_layer_mb <= 0:
            raise ValueError("Cannot calculate per-layer memory")

        usable_vram = available_vram_mb * self.VRAM_SAFETY_FACTOR

        gpu_layers = max(0, int(usable_vram / per_layer_mb))
        cpu_layers = self.metadata.num_hidden_layers - gpu_layers

        # If no layers fit but VRAM could hold at least one, force one layer
        if gpu_layers == 0 and available_vram_mb > per_layer_mb:
            gpu_layers = 1
            cpu_layers = self.metadata.num_hidden_layers - 1

        total_memory = self.calculate_total_model_memory()

        return GPULayerCalculation(
            total_layers=self.metadata.num_hidden_layers,
            gpu_layers=gpu_layers,
            cpu_layers=cpu_layers,
            model_memory_mb=total_memory,
            available_vram_mb=available_vram_mb,
            per_layer_memory_mb=per_layer_mb,
        )
