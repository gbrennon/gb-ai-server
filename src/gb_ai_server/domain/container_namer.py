"""Container naming strategy."""

import re


class ContainerNamer:
    """Derive container names from model display names."""

    PREFIX: str = "llama"

    @classmethod
    def container_for_model(cls, model_display_name: str) -> str:
        """
        Derive container name from model display name.

        Converts "qwen2.5-coder:7b" → "llama-qwen25-coder"

        Args:
            model_display_name: Model display name (e.g., "qwen2.5-coder:7b").

        Returns:
            Container name in format "llama-<sanitized_name>".

        Raises:
            ValueError: If display name is empty.
        """
        if not model_display_name or not model_display_name.strip():
            raise ValueError("Model display name cannot be empty")

        # Remove colons and dots, replace with hyphens
        sanitized = model_display_name.replace(":", "-").replace(".", "")
        # Remove any remaining special characters except hyphens
        sanitized = re.sub(r"[^a-z0-9\-]", "", sanitized.lower())
        # Collapse multiple hyphens into single
        sanitized = re.sub(r"-+", "-", sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip("-")

        return f"{cls.PREFIX}-{sanitized}"
