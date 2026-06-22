"""Map model filenames to resource requirements."""

from .resource_requirements import ResourceRequirements


class ResourceRequirementsMapper:
    """Map model filenames to resource requirements."""

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

    @staticmethod
    def _sorted_patterns() -> list[tuple[str, ResourceRequirements]]:
        return sorted(
            ResourceRequirementsMapper._REQUIREMENTS.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    @staticmethod
    def requirements_for_model(filename: str) -> ResourceRequirements:
        filename_lower = filename.lower()

        for size_pattern, requirements in ResourceRequirementsMapper._sorted_patterns():
            if size_pattern in filename_lower:
                return requirements

        return ResourceRequirements(
            size_gb=12,
            vram_needed_gb=12,
            context_size=4096,
            gpu_layers=999,
        )
