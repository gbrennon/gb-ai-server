"""Integration tests for Podman compose adapters (fixture scripts, no real tools)."""

from pathlib import Path

from gb_ai_server.infrastructure.executors.podman import PodmanComposeStandalone
from gb_ai_server.infrastructure.executors.podman import PodmanComposeStandaloneLifecycle
from gb_ai_server.infrastructure.executors.podman import PodmanComposeStandaloneQuery
from gb_ai_server.infrastructure.executors.podman import PodmanComposeBuiltin
from gb_ai_server.infrastructure.executors.podman import PodmanComposeBuiltinLifecycle
from gb_ai_server.infrastructure.executors.podman import PodmanComposeBuiltinQuery
from tests.gb_ai_server.helpers import make_script, install_podman_compose


# ---------------------------------------------------------------------------
# PodmanComposeStandalone – Runtime
# ---------------------------------------------------------------------------


class TestPodmanComposeStandalone:
    def test_name(self) -> None:
        tool = PodmanComposeStandalone()
        assert tool.name == "podman-compose"

    def test_pretty_name(self) -> None:
        tool = PodmanComposeStandalone()
        assert "standalone" in tool.pretty_name

    def test_is_available_when_installed(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman-compose", stdout="version", exit_code=0)
        assert PodmanComposeStandalone().is_available() is True

    def test_is_available_false_when_missing(self, fake_bin: Path) -> None:
        assert PodmanComposeStandalone().is_available() is False


# ---------------------------------------------------------------------------
# PodmanComposeStandalone – Lifecycle
# ---------------------------------------------------------------------------


class TestPodmanComposeStandaloneLifecycle:
    def test_up(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="up ok", exit_code=0)
        result = PodmanComposeStandaloneLifecycle().up(Path("compose.yml"))
        assert result.success is True

    def test_up_with_services(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="up ok", exit_code=0)
        result = PodmanComposeStandaloneLifecycle().up(Path("compose.yml"), "web", "db")
        assert result.success is True

    def test_down(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="down ok", exit_code=0)
        result = PodmanComposeStandaloneLifecycle().down(Path("compose.yml"))
        assert result.success is True

    def test_restart(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="restart ok", exit_code=0)
        result = PodmanComposeStandaloneLifecycle().restart(Path("compose.yml"))
        assert result.success is True

    def test_restart_with_services(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="restart ok", exit_code=0)
        result = PodmanComposeStandaloneLifecycle().restart(Path("compose.yml"), "web")
        assert result.success is True


# ---------------------------------------------------------------------------
# PodmanComposeStandalone – Query
# ---------------------------------------------------------------------------


class TestPodmanComposeStandaloneQuery:
    def test_validate(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="config ok", exit_code=0)
        result = PodmanComposeStandaloneQuery().validate(Path("compose.yml"))
        assert result.success is True

    def test_ps(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="CONTAINER  STATUS", exit_code=0)
        result = PodmanComposeStandaloneQuery().ps(Path("compose.yml"))
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeStandaloneQuery().logs(Path("compose.yml"))
        assert result.success is True

    def test_logs_with_follow(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeStandaloneQuery().logs(Path("compose.yml"), follow=True)
        assert result.success is True

    def test_logs_with_service(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeStandaloneQuery().logs(Path("compose.yml"), service="web")
        assert result.success is True


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
