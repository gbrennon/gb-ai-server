"""Outbound port - compose tool detector."""

from typing import Protocol

from .compose_detection import ComposeDetection


class ComposeToolDetector(Protocol):
    """Protocol for detecting available compose tool."""

    def detect(self) -> ComposeDetection: ...
