"""Container naming strategy."""

import re


class ContainerNamer:
    """Derive container names from model display names."""

    PREFIX: str = "llama"

    @staticmethod
    def container_for_model(model_display_name: str) -> str:
        if not model_display_name or not model_display_name.strip():
            raise ValueError("Model display name cannot be empty")

        sanitized = ContainerNamer._replace_separators(model_display_name)
        sanitized = ContainerNamer._remove_special_chars(sanitized)
        sanitized = ContainerNamer._collapse_hyphens(sanitized)
        sanitized = ContainerNamer._strip_outer_hyphens(sanitized)

        return f"{ContainerNamer.PREFIX}-{sanitized}"

    @staticmethod
    def _replace_separators(name: str) -> str:
        return name.replace(":", "-").replace(".", "")

    @staticmethod
    def _remove_special_chars(name: str) -> str:
        return re.sub(r"[^a-z0-9\-]", "", name.lower())

    @staticmethod
    def _collapse_hyphens(name: str) -> str:
        return re.sub(r"-+", "-", name)

    @staticmethod
    def _strip_outer_hyphens(name: str) -> str:
        return name.strip("-")
