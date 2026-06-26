"""Podman-compose standalone tool availability."""

from ...application.ports.outbound import ComposeTool
from ..command import Command


class PodmanComposeStandalone(ComposeTool):
    """Podman-compose standalone runtime check."""

    @property
    def name(self) -> str:
        return "podman-compose"

    @property
    def pretty_name(self) -> str:
        return "podman-compose (standalone)"

    def is_available(self) -> bool:
        return Command.exists("podman-compose")
