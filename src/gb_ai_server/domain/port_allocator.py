"""Port allocation strategy (single-model server)."""

import os


class PortAllocator:
    """Fixed port for the single llama.cpp instance.

    The port can be overridden via the LLAMA_PORT environment variable.
    """

    DEFAULT_PORT: int = 8081

    @staticmethod
    def port() -> int:
        raw = os.environ.get("LLAMA_PORT")
        if raw is not None:
            try:
                return int(raw.strip())
            except (ValueError, TypeError):
                pass
        return PortAllocator.DEFAULT_PORT

