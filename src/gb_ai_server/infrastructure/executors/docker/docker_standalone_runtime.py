"""Docker-compose standalone tool availability."""

from ....application.ports.outbound import ComposeTool
from ...command import Command


class DockerComposeStandalone(ComposeTool):
    """Docker-compose standalone runtime check."""

    @property
    def name(self) -> str:
        return "docker-compose"

    @property
    def pretty_name(self) -> str:
        return "docker-compose (standalone)"

    def is_available(self) -> bool:
        return Command.exists("docker-compose")
