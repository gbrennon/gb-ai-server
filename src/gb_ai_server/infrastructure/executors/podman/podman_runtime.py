"""Podman container runtime availability adapter."""

from ....application.ports.outbound import ContainerRuntime
from ...command import Command


class PodmanRuntime(ContainerRuntime):
    """Podman runtime availability check."""

    @property
    def name(self) -> str:
        return "podman"

    @property
    def pretty_name(self) -> str:
        return "Podman"

    def is_available(self) -> bool:
        if not Command.exists("podman"):
            return False
        result = Command.run("podman", "ps", capture_output=True)
        return result.success
