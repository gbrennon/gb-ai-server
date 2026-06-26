"""Docker built-in compose tool availability."""

from ...application.ports.outbound import ComposeTool
from ..command import Command


class DockerComposeBuiltin(ComposeTool):
    """Docker built-in compose runtime check."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def pretty_name(self) -> str:
        return "Docker (built-in compose)"

    def is_available(self) -> bool:
        if not Command.exists("docker"):
            return False
        result = Command.run("docker", "compose", "version", capture_output=True)
        return result.success
