"""Shell command execution and validation."""

import subprocess

from ...domain import CommandResult


class Command:
    """Shell command execution and validation."""

    @staticmethod
    def exists(name: str) -> bool:
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
        except FileNotFoundError:
            return CommandResult(
                returncode=127,
                stdout="",
                stderr=f"Command not found: {args[0] if args else ''}",
                success=False,
            )

    @staticmethod
    def require(
        name: str,
        message: str | None = None,
    ) -> None:
        if not Command.exists(name):
            msg = f"Command not found: {name}"
            if message:
                msg += f". {message}"
            raise ValueError(msg)
