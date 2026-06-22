"""Colorized structured logger."""

from typing import TextIO
import sys
import subprocess

from .level import LogLevel


class TerminalLogger:
    """Structured logging with optional terminal colorization."""

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
        stream_out: TextIO | None = None,
        stream_err: TextIO | None = None,
    ) -> None:
        self.stream_out = stream_out or sys.stdout
        self.stream_err = stream_err or sys.stderr
        self.use_color = (
            use_color
            if use_color is not None
            else self._detect_tty_color()
        )

    @staticmethod
    def _detect_tty_color() -> bool:
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
        self._log(LogLevel.DEBUG, message, self.stream_out)

    def info(self, message: str) -> None:
        self._log(LogLevel.INFO, message, self.stream_out)

    def ok(self, message: str) -> None:
        self._log(LogLevel.OK, message, self.stream_out)

    def warn(self, message: str) -> None:
        self._log(LogLevel.WARN, message, self.stream_err)

    def error(self, message: str) -> None:
        self._log(LogLevel.ERROR, message, self.stream_err)

    def section(self, title: str) -> None:
        separator = "\u2500" * (len(title) + 4)
        print(f"\n{separator}", file=self.stream_out)
        print(f" {title}", file=self.stream_out)
        print(f"{separator}", file=self.stream_out)
