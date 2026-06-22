"""Outbound port - compose tool detector."""

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .compose_tool import ComposeTool


class ComposeToolDetector(Protocol):
    """Protocol for detecting available compose tool."""

    def detect(self) -> "ComposeTool": ...
