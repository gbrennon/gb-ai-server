"""Container information data class."""

from dataclasses import dataclass


@dataclass
class ContainerInfo:
    """Container information data class."""

    name: str
    image: str
    status: str
    ports: dict[int, int]
