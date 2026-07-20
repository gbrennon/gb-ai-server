"""CDI (Container Device Interface) service for GPU passthrough."""

from .cdi_service import CdiService, CdiStatus

__all__: list[str] = [
    "CdiService",
    "CdiStatus",
]
