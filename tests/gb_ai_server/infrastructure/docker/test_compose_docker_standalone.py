"""Integration tests for DockerComposeStandalone adapter classes."""

from pathlib import Path

from gb_ai_server.infrastructure.docker import DockerComposeStandalone
from gb_ai_server.infrastructure.docker import DockerComposeStandaloneLifecycle
from gb_ai_server.infrastructure.docker import DockerComposeStandaloneQuery
from tests.gb_ai_server.helpers import make_script, install_docker_compose


# ---------------------------------------------------------------------------
# DockerComposeStandalone – Runtime
# ---------------------------------------------------------------------------


class TestDockerComposeStandalone:
    def test_name(self) -> None:
        tool = DockerComposeStandalone()
        assert tool.name == "docker-compose"

    def test_is_available_when_installed(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker-compose", stdout="version", exit_code=0)
        assert DockerComposeStandalone().is_available() is True

    def test_is_available_false_when_missing(self, fake_bin: Path) -> None:
        assert DockerComposeStandalone().is_available() is False


# ---------------------------------------------------------------------------
# DockerComposeStandalone – Lifecycle
# ---------------------------------------------------------------------------


class TestDockerComposeStandaloneLifecycle:
    def test_up(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandaloneLifecycle().up(Path("compose.yml"))
        assert result.success is True

    def test_up_with_detach_false(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker-compose", stdout="up ok", exit_code=0)
        result = DockerComposeStandaloneLifecycle().up(Path("compose.yml"), detach=False)
        assert result.success is True

    def test_down(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandaloneLifecycle().down(Path("compose.yml"))
        assert result.success is True

    def test_restart(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandaloneLifecycle().restart(Path("compose.yml"))
        assert result.success is True


# ---------------------------------------------------------------------------
# DockerComposeStandalone – Query
# ---------------------------------------------------------------------------


class TestDockerComposeStandaloneQuery:
    def test_validate(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandaloneQuery().validate(Path("compose.yml"))
        assert result.success is True

    def test_ps(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandaloneQuery().ps(Path("compose.yml"))
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandaloneQuery().logs(Path("compose.yml"))
        assert result.success is True