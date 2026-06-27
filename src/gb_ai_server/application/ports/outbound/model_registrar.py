"""Outbound port - model registrar interface."""

from typing import Protocol


class ModelRegistrar(Protocol):
    """Register a local model with agentic coding tools."""

    def register_model(
        self,
        model: tuple[str, str, int, str],
        provider_base_url: str | None = None,
    ) -> bool:
        ...

    def is_registered(self, model_name: str) -> bool:
        ...
