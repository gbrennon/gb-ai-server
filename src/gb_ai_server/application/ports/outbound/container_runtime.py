"""Outbound port - container runtime interface."""

from abc import ABC, abstractmethod


class ContainerRuntime(ABC):
    """Abstract container runtime interface."""

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
