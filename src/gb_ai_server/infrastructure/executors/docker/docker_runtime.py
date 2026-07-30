"""Docker container runtime availability adapter."""

from ....application.ports.outbound import ContainerRuntime
from ...command import Command


class DockerRuntime(ContainerRuntime):
    """Docker runtime availability check."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def pretty_name(self) -> str:
        return "Docker"

    def is_available(self) -> bool:
        if not Command.exists("docker"):
            return False
        result = Command.run("docker", "ps", capture_output=True)
        return result.success
