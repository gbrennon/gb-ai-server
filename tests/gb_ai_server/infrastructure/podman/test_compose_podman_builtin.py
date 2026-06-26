"""Integration tests for PodmanComposeBuiltin adapter classes."""

from pathlib import Path

from gb_ai_server.infrastructure.podman import PodmanComposeBuiltin
from gb_ai_server.infrastructure.podman import PodmanComposeBuiltinLifecycle
from gb_ai_server.infrastructure.podman import PodmanComposeBuiltinQuery
from tests.gb_ai_server.helpers import make_script, install_podman_compose


# ---------------------------------------------------------------------------
# PodmanComposeBuiltin – Runtime
# ---------------------------------------------------------------------------


class TestPodmanComposeBuiltin:
    def test_name(self) -> None:
        tool = PodmanComposeBuiltin()
        assert tool.name == "podman"

    def test_pretty_name(self) -> None:
        tool = PodmanComposeBuiltin()
        assert "built-in" in tool.pretty_name

    def test_is_available_when_installed(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="version ok", exit_code=0)
        assert PodmanComposeBuiltin().is_available() is True

    def test_is_available_false_when_missing(self, fake_bin: Path) -> None:
        assert PodmanComposeBuiltin().is_available() is False


# ---------------------------------------------------------------------------
# PodmanComposeBuiltin – Lifecycle
# ---------------------------------------------------------------------------


class TestPodmanComposeBuiltinLifecycle:
    def test_up(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="up ok", exit_code=0)
        result = PodmanComposeBuiltinLifecycle().up(Path("compose.yml"))
        assert result.success is True

    def test_down(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="down ok", exit_code=0)
        result = PodmanComposeBuiltinLifecycle().down(Path("compose.yml"))
        assert result.success is True

    def test_restart(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="restart ok", exit_code=0)
        result = PodmanComposeBuiltinLifecycle().restart(Path("compose.yml"))
        assert result.success is True


# ---------------------------------------------------------------------------
# PodmanComposeBuiltin – Query
# ---------------------------------------------------------------------------


class TestPodmanComposeBuiltinQuery:
    def test_validate(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="config ok", exit_code=0)
        result = PodmanComposeBuiltinQuery().validate(Path("compose.yml"))
        assert result.success is True

    def test_ps(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="CONTAINER  STATUS", exit_code=0)
        result = PodmanComposeBuiltinQuery().ps(Path("compose.yml"))
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeBuiltinQuery().logs(Path("compose.yml"))
        assert result.success is True

    def test_logs_with_follow(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeBuiltinQuery().logs(Path("compose.yml"), follow=True)
        assert result.success is True

    def test_logs_with_service(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeBuiltinQuery().logs(Path("compose.yml"), service="web")
        assert result.success is True