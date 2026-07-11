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

    @staticmethod
    def context_size_for_model(filename: str) -> int:
        """Resolve context window using GGUF metadata when file is available."""
        import os
        from gb_ai_server.infrastructure.persistence.gguf_reader import read_context_window

        # Try GGUF file in known locations
        search_dirs = os.environ.get("MODEL_DIRS", os.environ.get("MODELS_DIR", "")).split(":")
        search_dirs = [d for d in search_dirs if d]
        search_dirs.append(os.getcwd())

        for base in search_dirs:
            candidate = os.path.join(base, filename)
            if os.path.exists(candidate):
                ctx = read_context_window(candidate)
                if ctx:
                    return ctx

        # Fall back to pattern-based estimation
        return ResourceRequirementsMapper.requirements_for_model(filename).context_size
