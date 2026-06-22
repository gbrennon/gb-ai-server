"""Integration tests for compose adapters (fixture scripts, no real tools)."""

from pathlib import Path

from gb_ai_server.infrastructure.compose.podman_standalone import PodmanComposeStandalone
from gb_ai_server.infrastructure.compose.podman_builtin import PodmanComposeBuiltin
from gb_ai_server.infrastructure.compose.docker_standalone import DockerComposeStandalone
from gb_ai_server.infrastructure.compose.docker_builtin import DockerComposeBuiltin
from tests.helpers import make_script, install_podman_compose, install_docker_compose


# ---------------------------------------------------------------------------
# PodmanComposeStandalone
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

    def test_validate(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="config ok", exit_code=0)
        result = PodmanComposeStandalone().validate(Path("compose.yml"))
        assert result.success is True

    def test_up(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="up ok", exit_code=0)
        result = PodmanComposeStandalone().up(Path("compose.yml"))
        assert result.success is True

    def test_up_with_services(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="up ok", exit_code=0)
        result = PodmanComposeStandalone().up(Path("compose.yml"), "web", "db")
        assert result.success is True

    def test_down(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="down ok", exit_code=0)
        result = PodmanComposeStandalone().down(Path("compose.yml"))
        assert result.success is True

    def test_restart(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="restart ok", exit_code=0)
        result = PodmanComposeStandalone().restart(Path("compose.yml"))
        assert result.success is True

    def test_restart_with_services(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="restart ok", exit_code=0)
        result = PodmanComposeStandalone().restart(Path("compose.yml"), "web")
        assert result.success is True

    def test_ps(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="CONTAINER  STATUS", exit_code=0)
        result = PodmanComposeStandalone().ps(Path("compose.yml"))
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeStandalone().logs(Path("compose.yml"))
        assert result.success is True

    def test_logs_with_follow(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeStandalone().logs(Path("compose.yml"), follow=True)
        assert result.success is True

    def test_logs_with_service(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman-compose", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeStandalone().logs(Path("compose.yml"), service="web")
        assert result.success is True


# ---------------------------------------------------------------------------
# PodmanComposeBuiltin
# ---------------------------------------------------------------------------


class TestPodmanComposeBuiltin:
    def test_name(self) -> None:
        tool = PodmanComposeBuiltin()
        assert tool.name == "podman-compose-builtin"

    def test_pretty_name(self) -> None:
        tool = PodmanComposeBuiltin()
        assert "built-in" in tool.pretty_name

    def test_is_available_when_installed(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        # Builtin checks `podman compose version`
        make_script(fake_bin, "podman", stdout="version ok", exit_code=0)
        assert PodmanComposeBuiltin().is_available() is True

    def test_is_available_false_when_missing(self, fake_bin: Path) -> None:
        assert PodmanComposeBuiltin().is_available() is False

    def test_validate(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="config ok", exit_code=0)
        result = PodmanComposeBuiltin().validate(Path("compose.yml"))
        assert result.success is True

    def test_up(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="up ok", exit_code=0)
        result = PodmanComposeBuiltin().up(Path("compose.yml"))
        assert result.success is True

    def test_down(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="down ok", exit_code=0)
        result = PodmanComposeBuiltin().down(Path("compose.yml"))
        assert result.success is True

    def test_restart(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="restart ok", exit_code=0)
        result = PodmanComposeBuiltin().restart(Path("compose.yml"))
        assert result.success is True

    def test_ps(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="CONTAINER  STATUS", exit_code=0)
        result = PodmanComposeBuiltin().ps(Path("compose.yml"))
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeBuiltin().logs(Path("compose.yml"))
        assert result.success is True

    def test_logs_with_follow(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeBuiltin().logs(Path("compose.yml"), follow=True)
        assert result.success is True

    def test_logs_with_service(self, fake_bin: Path) -> None:
        install_podman_compose(fake_bin)
        make_script(fake_bin, "podman", stdout="[INFO] log", exit_code=0)
        result = PodmanComposeBuiltin().logs(Path("compose.yml"), service="web")
        assert result.success is True


# ---------------------------------------------------------------------------
# DockerComposeStandalone
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

    def test_validate(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandalone().validate(Path("compose.yml"))
        assert result.success is True

    def test_up(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandalone().up(Path("compose.yml"))
        assert result.success is True

    def test_down(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandalone().down(Path("compose.yml"))
        assert result.success is True

    def test_restart(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandalone().restart(Path("compose.yml"))
        assert result.success is True

    def test_ps(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandalone().ps(Path("compose.yml"))
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeStandalone().logs(Path("compose.yml"))
        assert result.success is True

    def test_up_with_detach_false(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker-compose", stdout="up ok", exit_code=0)
        result = DockerComposeStandalone().up(Path("compose.yml"), detach=False)
        assert result.success is True


# ---------------------------------------------------------------------------
# DockerComposeBuiltin
# ---------------------------------------------------------------------------


class TestDockerComposeBuiltin:
    def test_name(self) -> None:
        tool = DockerComposeBuiltin()
        assert tool.name == "docker-compose-builtin"

    def test_pretty_name(self) -> None:
        tool = DockerComposeBuiltin()
        assert "built-in" in tool.pretty_name

    def test_is_available_when_installed(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker", stdout="docker compose version", exit_code=0)
        assert DockerComposeBuiltin().is_available() is True

    def test_is_available_false_when_missing(self, fake_bin: Path) -> None:
        assert DockerComposeBuiltin().is_available() is False

    def test_validate(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltin().validate(Path("compose.yml"))
        assert result.success is True

    def test_up(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltin().up(Path("compose.yml"))
        assert result.success is True

    def test_down(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltin().down(Path("compose.yml"))
        assert result.success is True

    def test_restart(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltin().restart(Path("compose.yml"))
        assert result.success is True

    def test_ps(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        result = DockerComposeBuiltin().ps(Path("compose.yml"))
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        install_docker_compose(fake_bin)
        make_script(fake_bin, "docker", stdout="[INFO] logs", exit_code=0)
        result = DockerComposeBuiltin().logs(Path("compose.yml"))
        assert result.success is True
