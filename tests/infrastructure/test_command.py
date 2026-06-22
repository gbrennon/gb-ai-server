"""Integration tests for Command (fixture scripts, no real system commands)."""

from pathlib import Path

import pytest

from gb_ai_server.infrastructure.command import Command, CommandResult
from tests.helpers import make_script


class TestCommandRun:
    def test_echo_script(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-echo", stdout="hello world")
        result = Command.run("test-echo", capture_output=True)
        assert result.stdout == "hello world\n"
        assert result.returncode == 0
        assert result.success is True

    def test_failing_script(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-fail", stderr="error msg", exit_code=1)
        result = Command.run("test-fail", capture_output=True)
        assert result.success is False
        assert result.returncode == 1
        assert "error msg" in result.stderr

    def test_captured_stdout(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-cap", stdout="line1\nline2")
        result = Command.run("test-cap", capture_output=True)
        assert result.stdout == "line1\nline2\n"

    def test_run_without_capture(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-silent", exit_code=0)
        result = Command.run("test-silent", capture_output=False)
        assert result.returncode == 0
        assert result.success is True

    def test_multiple_args(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-args", stdout="processed")
        result = Command.run("test-args", "-f", "compose.yml", capture_output=True)
        assert result.stdout == "processed\n"
        assert result.success is True

    def test_check_true_does_not_raise_on_success(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-ok", exit_code=0)
        result = Command.run("test-ok", check=True, capture_output=True)
        assert result.success is True

    def test_check_true_with_failure(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-check-fail", stderr="fail", exit_code=2)
        result = Command.run("test-check-fail", check=True, capture_output=True)
        assert result.success is False
        assert result.returncode == 2

    def test_non_existent_command(self) -> None:
        result = Command.run("this-command-does-not-exist-xyz", capture_output=True)
        assert result.success is False
        assert result.returncode == 127
        assert "not found" in result.stderr


class TestCommandExists:
    def test_existing_command(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-tool", exit_code=0)
        assert Command.exists("test-tool") is True

    def test_nonexistent_command(self) -> None:
        assert Command.exists("this-does-not-exist-xyz") is False


class TestCommandRequire:
    def test_known_command_does_not_raise(self, fake_bin: Path) -> None:
        make_script(fake_bin, "test-req", exit_code=0)
        Command.require("test-req")

    def test_unknown_command_raises(self) -> None:
        with pytest.raises(ValueError, match="Command not found"):
            Command.require("nonexistent-xyz")

    def test_unknown_command_with_custom_message(self) -> None:
        with pytest.raises(ValueError, match="custom message"):
            Command.require("nonexistent-xyz", message="custom message")


class TestCommandResult:
    def test_bool_true_on_success(self) -> None:
        result = CommandResult(returncode=0, stdout="", stderr="", success=True)
        assert bool(result) is True

    def test_bool_false_on_failure(self) -> None:
        result = CommandResult(returncode=1, stdout="", stderr="", success=False)
        assert bool(result) is False

    def test_attributes(self) -> None:
        result = CommandResult(0, "out", "err", True)
        assert result.returncode == 0
        assert result.stdout == "out"
        assert result.stderr == "err"
