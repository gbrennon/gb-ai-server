"""Logging infrastructure for llama bootstrap system."""

from enum import Enum
from typing import TextIO
import sys
import subprocess


class LogLevel(Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"


class Logger:
    """Structured logging with optional colorization."""

    _COLOR_CODES: dict[LogLevel, int] = {
        LogLevel.DEBUG: 7,
        LogLevel.INFO: 4,
        LogLevel.OK: 2,
        LogLevel.WARN: 3,
        LogLevel.ERROR: 1,
    }

    def __init__(
        self,
        use_color: bool | None = None,
        stream_out: TextIO = sys.stdout,
        stream_err: TextIO = sys.stderr,
    ) -> None:
        """
        Initialize logger.

        Args:
            use_color: Enable colorization. If None, auto-detect from TTY.
            stream_out: Output stream for info/ok messages.
            stream_err: Output stream for warn/error messages.
        """
        self.stream_out = stream_out
        self.stream_err = stream_err
        self.use_color = (
            use_color
            if use_color is not None
            else self._detect_tty_color()
        )

    @staticmethod
    def _detect_tty_color() -> bool:
        """Auto-detect color support from TTY."""
        if not sys.stdout.isatty():
            return False
        try:
            result = subprocess.run(
                ["tput", "colors"],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _colorize(self, level: LogLevel, text: str) -> str:
        """Apply color codes to text if enabled."""
        if not self.use_color:
            return text

        color_code = self._COLOR_CODES[level]
        try:
            bold_on = subprocess.run(
                ["tput", "bold"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout
            color_on = subprocess.run(
                ["tput", "setaf", str(color_code)],
                capture_output=True,
                text=True,
                check=False,
            ).stdout
            reset = subprocess.run(
                ["tput", "sgr0"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout
            return f"{bold_on}{color_on}{text}{reset}"
        except Exception:
            return text

    def _log(
        self,
        level: LogLevel,
        message: str,
        stream: TextIO,
    ) -> None:
        """Log a message with level prefix."""
        prefix_map = {
            LogLevel.DEBUG: "[DEBUG]",
            LogLevel.INFO: "[INFO ]",
            LogLevel.OK: "[ OK ]",
            LogLevel.WARN: "[WARN ]",
            LogLevel.ERROR: "[ERROR]",
        }
        prefix = prefix_map[level]
        formatted = f"{prefix}  {message}"
        colored = self._colorize(level, formatted)
        print(colored, file=stream)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, self.stream_out)

    def info(self, message: str) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, self.stream_out)

    def ok(self, message: str) -> None:
        """Log success message."""
        self._log(LogLevel.OK, message, self.stream_out)

    def warn(self, message: str) -> None:
        """Log warning message."""
        self._log(LogLevel.WARN, message, self.stream_err)

    def error(self, message: str) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, self.stream_err)

    def section(self, title: str) -> None:
        """Log section header."""
        separator = "─" * (len(title) + 4)
        print(f"\n{separator}", file=self.stream_out)
        print(f" {title}", file=self.stream_out)
        print(f"{separator}", file=self.stream_out)
