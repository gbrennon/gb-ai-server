"""Shared test configuration and fixtures.

Infrastructure tests use fixture scripts instead of real system commands.
Fixture scripts are created in temporary directories and added to PATH,
so the real implementation code executes against controlled environments.
"""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from gb_ai_server.domain import CommandResult


# ---------------------------------------------------------------------------
# Fixture script helpers — create fake executables in temp dirs
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_bin(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary bin/ directory isolated from host PATH.

    PATH is set to *fake_bin/bin* only. A *which* helper script is
    installed that only searches the fake bin dir, so host tools
    are invisible to ``Command.exists``.

    Tests install fixture scripts (podman, docker, curl, …) into
    *bin_dir* to simulate real system commands.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    old_path = __import__("os").environ.copy().get("PATH", "")
    __import__("os").environ["PATH"] = str(bin_dir)
    _install_which_helper(bin_dir)
    try:
        yield bin_dir
    finally:
        __import__("os").environ["PATH"] = old_path


def _install_which_helper(bin_dir: Path) -> None:
    """Install a *which* script that only searches *bin_dir*."""
    script = '#!/bin/sh\ndir="${0%/*}"\nfor cmd in "$@"; do\n    if [ -x "$dir/$cmd" ]; then\n        echo "$dir/$cmd"\n        exit 0\n    fi\ndone\nexit 1\n'
    path = bin_dir / "which"
    path.write_text(script)
    path.chmod(0o755)





# ---------------------------------------------------------------------------
# Mock builders for application-layer tests (still use mocks — that's correct)
# ---------------------------------------------------------------------------


def make_logger_mock() -> MagicMock:
    """Create a mock Logger that records all calls."""
    return MagicMock()


def make_http_client_mock(healthy: bool = True) -> MagicMock:
    """Create a mock HttpClient that returns *healthy*."""
    client = MagicMock()
    client.get.return_value = healthy
    return client


def make_model_downloader_mock(success: bool = True) -> MagicMock:
    """Create a mock ModelDownloader."""
    d = MagicMock()
    d.download.return_value = success
    d.exists.return_value = success
    return d


def make_compose_tool_mock(
    validate_ok: bool = True,
    up_ok: bool = True,
    down_ok: bool = True,
    restart_ok: bool = True,
    ps_ok: bool = True,
    logs_ok: bool = True,
) -> MagicMock:
    """Create a mock ComposeTool with configurable CommandResult returns."""
    tool = MagicMock()
    tool.name = "podman-compose"
    tool.pretty_name = "Podman Compose (Standalone)"
    tool.is_available.return_value = True
    tool.validate.return_value = CommandResult(
        returncode=0 if validate_ok else 1,
        stdout="" if validate_ok else "",
        stderr="" if validate_ok else "invalid",
        success=validate_ok,
    )
    tool.up.return_value = CommandResult(
        returncode=0 if up_ok else 1,
        stdout="Container running",
        stderr="" if up_ok else "failed",
        success=up_ok,
    )
    tool.down.return_value = CommandResult(
        returncode=0 if down_ok else 1,
        stdout="" if down_ok else "",
        stderr="" if down_ok else "failed",
        success=down_ok,
    )
    tool.restart.return_value = CommandResult(
        returncode=0 if restart_ok else 1,
        stdout="Restarted",
        stderr="" if restart_ok else "failed",
        success=restart_ok,
    )
    tool.ps.return_value = CommandResult(
        returncode=0 if ps_ok else 1,
        stdout="CONTAINER ID  IMAGE  COMMAND  CREATED  STATUS  PORTS  NAMES\nabc  llama-coder  ...  5s ago  Up 5s  8081  llama-coder",
        stderr="" if ps_ok else "failed",
        success=ps_ok,
    )
    tool.logs.return_value = CommandResult(
        returncode=0 if logs_ok else 1,
        stdout="[INFO] Server started" if logs_ok else "",
        stderr="" if logs_ok else "failed",
        success=logs_ok,
    )
    return tool


def make_container_runtime_mock(
    available: bool = True,
    running: bool = True,
) -> MagicMock:
    """Create a mock ContainerRuntime."""
    rt = MagicMock()
    rt.name = "podman"
    rt.pretty_name = "Podman"
    rt.is_available.return_value = available
    rt.is_running.return_value = running
    rt.exec.return_value = CommandResult(
        returncode=0, stdout="output", stderr="", success=True
    )
    rt.copy_to.return_value = CommandResult(
        returncode=0, stdout="", stderr="", success=True
    )
    rt.ps.return_value = CommandResult(
        returncode=0,
        stdout="CONTAINER ID  IMAGE  COMMAND  CREATED  STATUS  PORTS  NAMES\nabc  llama-coder  ...  5s ago  Up 5s  8081  llama-coder",
        stderr="",
        success=True,
    )
    rt.logs.return_value = CommandResult(
        returncode=0,
        stdout="[INFO] Server started",
        stderr="",
        success=True,
    )
    return rt


def make_runtime_detector_mock(runtime: Any = None) -> MagicMock:
    """Create a mock RuntimeDetector."""
    d = MagicMock()
    d.detect.return_value = runtime or make_container_runtime_mock()
    return d


def make_compose_detector_mock(tool: Any = None) -> MagicMock:
    """Create a mock ComposeToolDetector."""
    d = MagicMock()
    d.detect.return_value = tool or make_compose_tool_mock()
    return d


# ---------------------------------------------------------------------------
# Shared filesystem fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fixture_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Temporary directory for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    yield data_dir
