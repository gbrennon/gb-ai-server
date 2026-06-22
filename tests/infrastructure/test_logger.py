"""Integration tests for TerminalLogger colorization (real tput subprocess)."""

import sys
import io

from gb_ai_server.infrastructure.logging import TerminalLogger, LogLevel


class TestTerminalLoggerColor:
    def test_colorize_applies_ansi_when_use_color_true(self) -> None:
        logger = TerminalLogger(use_color=True)
        colored = logger._colorize(LogLevel.INFO, "hello")
        assert "\x1b[" in colored
        assert "hello" in colored

    def test_colorize_returns_plain_when_use_color_false(self) -> None:
        logger = TerminalLogger(use_color=False)
        plain = logger._colorize(LogLevel.INFO, "hello")
        assert plain == "hello"

    def test_colorize_handles_all_levels(self) -> None:
        logger = TerminalLogger(use_color=True)
        for level in LogLevel:
            result = logger._colorize(level, "test")
            assert "test" in result

    def test_detect_tty_color_returns_false_when_not_tty(self) -> None:
        old_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO("")
            result = TerminalLogger._detect_tty_color()
            assert result is False
        finally:
            sys.stdin = old_stdin

    def test_section_output_format(self, capsys: object) -> None:
        logger = TerminalLogger(use_color=False)
        logger.section("Test")
        captured = capsys.readouterr()
        assert "\u2500" in captured.out
        assert "Test" in captured.out


class TestTerminalLoggerStreamInjection:
    def test_custom_streams(self) -> None:
        out = io.StringIO()
        err = io.StringIO()
        logger = TerminalLogger(use_color=False, stream_out=out, stream_err=err)
        logger.info("info msg")
        logger.warn("warn msg")
        assert "info msg" in out.getvalue()
        assert "warn msg" in err.getvalue()
