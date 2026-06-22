"""Outbound port - HTTP client for health checks."""

from typing import Protocol


class HttpClient(Protocol):
    """Protocol for making HTTP requests."""

    def get(self, url: str) -> bool:
        """Perform HTTP GET and return True on 2xx/healthy response."""
        ...
