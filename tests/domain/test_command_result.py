"""Tests for CommandResult domain object."""

from gb_ai_server.domain import CommandResult


class TestCommandResult:
    def test_success_is_true(self) -> None:
        result = CommandResult(returncode=0, stdout="ok", stderr="", success=True)
        assert bool(result) is True

    def test_failure_is_false(self) -> None:
        result = CommandResult(returncode=1, stdout="", stderr="err", success=False)
        assert bool(result) is False

    def test_attributes(self) -> None:
        result = CommandResult(returncode=0, stdout="out", stderr="err", success=True)
        assert result.returncode == 0
        assert result.stdout == "out"
        assert result.stderr == "err"
        assert result.success is True
