"""Integration tests for DockerComposeBuiltin adapter classes."""

from pathlib import Path

from gb_ai_server.infrastructure.executors.docker import DockerComposeBuiltin
from gb_ai_server.infrastructure.executors.docker import DockerComposeBuiltinLifecycle
from gb_ai_server.infrastructure.executors.docker import DockerComposeBuiltinQuery
from tests.gb_ai_server.helpers import make_script, install_docker_compose


# ---------------------------------------------------------------------------
# DockerComposeBuiltin – Runtime
# ---------------------------------------------------------------------------


class TestDockerComposeBuiltin:
    def test_name(self) -> None:
        tool = DockerComposeBuiltin()
        assert tool.name == "docker"

    def test_pretty_name(self) -> None:
        tool = DockerComposeBuiltin()
        assert "built-in" in tool.pretty_name

    def test_is_available_when_installed(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker", stdout="docker compose version", exit_code=0)
        assert DockerComposeBuiltin().is_available() is True

    def test_is_available_false_when_missing(self, fake_bin: Path) -> None:
        assert DockerComposeBuiltin().is_available() is False


# ---------------------------------------------------------------------------
# DockerComposeBuiltin – Lifecycle
# ---------------------------------------------------------------------------


class TestDockerComposeBuiltinLifecycle:
    def test_up(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltinLifecycle().up(Path("compose.yml"))
        assert result.success is True

    def test_down(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltinLifecycle().down(Path("compose.yml"))
        assert result.success is True

    def test_restart(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltinLifecycle().restart(Path("compose.yml"))
        assert result.success is True


# ---------------------------------------------------------------------------
# DockerComposeBuiltin – Query
# ---------------------------------------------------------------------------


class TestDockerComposeBuiltinQuery:
    def test_validate(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltinQuery().validate(Path("compose.yml"))
        assert result.success is True

    def test_ps(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker", stdout="CONTAINER  STATUS", exit_code=0)
        result = DockerComposeBuiltinQuery().ps(Path("compose.yml"))
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker", stdout="[INFO] logs", exit_code=0)
        result = DockerComposeBuiltinQuery().logs(Path("compose.yml"))
        assert result.success is True

    def test_logs_with_follow(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker", stdout="[INFO] logs", exit_code=0)
        result = DockerComposeBuiltinQuery().logs(Path("compose.yml"), follow=True)
        assert result.success is True

    def test_logs_with_service(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker", stdout="[INFO] logs", exit_code=0)
        result = DockerComposeBuiltinQuery().logs(Path("compose.yml"), service="web")
        assert result.success is True