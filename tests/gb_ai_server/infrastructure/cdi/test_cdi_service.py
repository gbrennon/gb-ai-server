"""Tests for CdiService (infrastructure-level, uses fake scripts)."""

from pathlib import Path

from gb_ai_server.infrastructure.cdi import CdiService
from gb_ai_server.infrastructure.logging import TerminalLogger
from tests.gb_ai_server.helpers import make_script


def _service() -> CdiService:
    return CdiService(TerminalLogger(use_color=False))


def _install_nvidia_ctk(bin_dir: Path, list_stdout: str = "", list_exit: int = 0,
                        gen_stdout: str = "ok", gen_exit: int = 0) -> None:
    """Install a fake nvidia-ctk that dispatches on subcommand."""
    script = (
        "#!/bin/sh\n"
        'if [ "$1" = "cdi" ] && [ "$2" = "generate" ]; then\n'
        f'  echo "{gen_stdout}"\n'
        f'  exit {gen_exit}\n'
        "fi\n"
        'if [ "$1" = "cdi" ] && [ "$2" = "list" ]; then\n'
        f'  echo "{list_stdout}"\n'
        f'  exit {list_exit}\n'
        "fi\n"
        "exit 1\n"
    )
    path = bin_dir / "nvidia-ctk"
    path.write_text(script)
    path.chmod(0o755)


def _install_nvidia_ctk_stateful(bin_dir: Path) -> None:
    """Install an nvidia-ctk that tracks state via a marker file.

    Before ``cdi generate``: ``cdi list`` returns no devices (exit 1).
    After ``cdi generate``: ``cdi list`` returns GPU devices (exit 0).
    """
    script = (
        "#!/bin/sh\n"
        f'MARKER="{bin_dir}/.cdi_generated"\n'
        'if [ "$1" = "cdi" ] && [ "$2" = "generate" ]; then\n'
        '  : > "$MARKER"\n'
        '  echo "CDI specs generated"\n'
        '  exit 0\n'
        "fi\n"
        'if [ "$1" = "cdi" ] && [ "$2" = "list" ]; then\n'
        '  if [ -f "$MARKER" ]; then\n'
        '    echo "nvidia.com/gpu=0"\n'
        '    exit 0\n'
        '  fi\n'
        '  echo "no CDI devices found"\n'
        '  exit 1\n'
        "fi\n"
        "exit 1\n"
    )
    path = bin_dir / "nvidia-ctk"
    path.write_text(script)
    path.chmod(0o755)


class TestCheck:
    def test_returns_active_when_gpu_found(self, fake_bin: Path) -> None:
        _install_nvidia_ctk(fake_bin, list_stdout="nvidia.com/gpu=0\nnvidia.com/gpu=all")
        status = _service().check()
        assert status.active is True
        assert "nvidia.com/gpu=0" in status.devices
        assert status.error is None

    def test_returns_inactive_when_no_gpu(self, fake_bin: Path) -> None:
        _install_nvidia_ctk(fake_bin, list_stdout="no CDI devices found", list_exit=1)
        status = _service().check()
        assert status.active is False

    def test_returns_inactive_on_nonzero_exit(self, fake_bin: Path) -> None:
        _install_nvidia_ctk(fake_bin, list_stdout="", list_exit=1)
        status = _service().check()
        assert status.active is False
        assert status.error is not None

    def test_returns_inactive_when_command_missing(self, fake_bin: Path) -> None:
        status = _service().check()
        assert status.active is False
        assert "not found" in (status.error or "")


class TestEnable:
    def test_generates_and_checks(self, fake_bin: Path) -> None:
        _install_nvidia_ctk(
            fake_bin,
            list_stdout="nvidia.com/gpu=0",
            gen_stdout="CDI specs generated",
        )
        status = _service().enable()
        assert status.active is True

    def test_returns_inactive_on_generate_failure(self, fake_bin: Path) -> None:
        _install_nvidia_ctk(fake_bin, list_exit=1, gen_exit=1)
        status = _service().enable()
        assert status.active is False
        assert status.error is not None

    def test_returns_inactive_when_command_missing(self, fake_bin: Path) -> None:
        status = _service().enable()
        assert status.active is False
        assert "not found" in (status.error or "")


class TestEnsure:
    def test_returns_active_when_already_active(self, fake_bin: Path) -> None:
        _install_nvidia_ctk(fake_bin, list_stdout="nvidia.com/gpu=0")
        status = _service().ensure()
        assert status.active is True

    def test_enables_and_becomes_active(self, fake_bin: Path) -> None:
        _install_nvidia_ctk_stateful(fake_bin)
        status = _service().ensure()
        assert status.active is True

    def test_reports_failure_when_generate_fails(self, fake_bin: Path) -> None:
        _install_nvidia_ctk(fake_bin, list_exit=1, gen_exit=1)
        status = _service().ensure()
        assert status.active is False

    def test_handles_missing_command(self, fake_bin: Path) -> None:
        status = _service().ensure()
        assert status.active is False


class TestCheckNvidiaSmi:
    def test_returns_true_when_gpu_found(self, fake_bin: Path) -> None:
        make_script(fake_bin, "nvidia-smi", stdout="GPU 0: NVIDIA GeForce RTX 5070", exit_code=0)
        assert _service().check_nvidia_smi() is True

    def test_returns_false_on_failure(self, fake_bin: Path) -> None:
        make_script(fake_bin, "nvidia-smi", stderr="no gpu", exit_code=1)
        assert _service().check_nvidia_smi() is False

    def test_returns_false_when_command_missing(self, fake_bin: Path) -> None:
        assert _service().check_nvidia_smi() is False
