"""Model resource requirements mapping."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceRequirements:
    """Resource requirements for a model."""

    size_gb: int
    vram_needed_gb: int
    context_size: int
    gpu_layers: int

    def __str__(self) -> str:
        """Format as pipe-separated string."""
        return (
            f"{self.size_gb} | "
            f"{self.vram_needed_gb} | "
            f"{self.context_size} | "
            f"{self.gpu_layers}"
        )
