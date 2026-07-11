"""Container naming strategy (single-model server)."""

import os


class ContainerNamer:
    """Derive the container name from the LLAMA_CONTAINER_NAME env var or default."""
    DEFAULT_NAME: str = "llama-coder"

    @staticmethod
    def name() -> str:
        return os.environ.get("LLAMA_CONTAINER_NAME", ContainerNamer.DEFAULT_NAME)

