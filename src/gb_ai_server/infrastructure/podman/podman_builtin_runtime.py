"""Podman built-in compose tool availability."""

from ...application.ports.outbound import ComposeTool
from ..command import Command


class PodmanComposeBuiltin(ComposeTool):
    """Podman built-in compose runtime check."""

    @property
    def name(self) -> str:
        return "podman"

    @property
    def pretty_name(self) -> str:
        return "Podman (built-in compose)"

    def is_available(self) -> bool:
        if not Command.exists("podman"):
            return False
        result = Command.run("podman", "compose", "version", capture_output=True)
        return result.success
