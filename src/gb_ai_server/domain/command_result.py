"""Command execution result — shared value object."""

from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a shell command execution."""

    returncode: int
    stdout: str
    stderr: str
    success: bool

    def __bool__(self) -> bool:
        return self.success
