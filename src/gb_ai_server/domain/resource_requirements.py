"""Model resource requirements mapping."""

from dataclasses import dataclass
import re


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


class ResourceRequirementsMapper:
    """Map model filenames to resource requirements."""

    # Model size patterns and their requirements
    _REQUIREMENTS: dict[str, ResourceRequirements] = {
        "7b": ResourceRequirements(
            size_gb=7,
            vram_needed_gb=8,
            context_size=8192,
            gpu_layers=999,
        ),
        "14b": ResourceRequirements(
            size_gb=14,
            vram_needed_gb=10,
            context_size=8192,
            gpu_layers=999,
        ),
        "24b": ResourceRequirements(
            size_gb=24,
            vram_needed_gb=16,
            context_size=4096,
            gpu_layers=999,
        ),
        "27b": ResourceRequirements(
            size_gb=27,
            vram_needed_gb=16,
            context_size=8192,
            gpu_layers=999,
        ),
    }

    @classmethod
    def requirements_for_model(cls, filename: str) -> ResourceRequirements:
        """
        Get resource requirements for model filename.

        Infers from model size in filename (7b, 14b, 24b, 27b).

        Args:
            filename: Model filename (e.g., "qwen-7b.gguf").

        Returns:
            ResourceRequirements.
        """
        filename_lower = filename.lower()

        # Try exact matches first
        for size_pattern, requirements in cls._REQUIREMENTS.items():
            if size_pattern in filename_lower:
                return requirements

        # Default for unknown sizes
        return ResourceRequirements(
            size_gb=12,
            vram_needed_gb=12,
            context_size=4096,
            gpu_layers=999,
        )
