"""Outbound port - compose tool interface."""

from abc import ABC, abstractmethod


class ComposeTool(ABC):
    """Abstract compose tool interface."""

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def pretty_name(self) -> str:
        pass
