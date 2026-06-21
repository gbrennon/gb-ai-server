"""Command execution and validation utilities."""

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class CommandResult:
    """Result of command execution."""

    returncode: int
    stdout: str
    stderr: str
    success: bool

    def __bool__(self) -> bool:
        """True if command succeeded."""
        return self.success


class Command:
    """Command execution and validation utilities."""

    @staticmethod
    def exists(name: str) -> bool:
        """
        Check if a command exists in PATH.

        Args:
            name: Command name.

        Returns:
            True if command exists.
        """
        result = subprocess.run(
            ["which", name],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    @staticmethod
    def run(
        *args: str,
        check: bool = False,
        capture_output: bool = False,
    ) -> CommandResult:
        """
        Execute a command.

        Args:
            args: Command and arguments.
            check: Raise exception on non-zero exit.
            capture_output: Capture stdout/stderr.

        Returns:
            CommandResult with returncode, stdout, stderr, success.

        Raises:
            subprocess.CalledProcessError: If check=True and command fails.
        """
        try:
            result = subprocess.run(
                args,
                check=check,
                capture_output=capture_output,
                text=True,
            )
            return CommandResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                success=result.returncode == 0,
            )
        except subprocess.CalledProcessError as e:
            return CommandResult(
                returncode=e.returncode,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                success=False,
            )

    @staticmethod
    def require(
        name: str,
        message: Optional[str] = None,
    ) -> None:
        """
        Require a command to exist, raise ValueError if not.

        Args:
            name: Command name.
            message: Error message to include.

        Raises:
            ValueError: If command not found.
        """
        if not Command.exists(name):
            msg = f"Command not found: {name}"
            if message:
                msg += f". {message}"
            raise ValueError(msg)
