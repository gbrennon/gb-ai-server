"""Integration tests for Docker runtime/inspector/operator adapters."""

from pathlib import Path

from gb_ai_server.infrastructure.executors.docker import DockerRuntime
from gb_ai_server.infrastructure.executors.docker import DockerInspector
from gb_ai_server.infrastructure.executors.docker import DockerOperator
from tests.gb_ai_server.helpers import make_script


class TestDockerRuntime:
    def test_name(self) -> None:
        rt = DockerRuntime()
        assert rt.name == "docker"

    def test_pretty_name(self) -> None:
        rt = DockerRuntime()
        assert rt.pretty_name == "Docker"

    def test_is_available_when_docker_works(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="CONTAINER ID", exit_code=0)
        rt = DockerRuntime()
        assert rt.is_available() is True

    def test_is_available_false_when_docker_missing(self) -> None:
        rt = DockerRuntime()
        assert rt.is_available() is False


class TestDockerInspector:
    def test_is_running_true(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="true", exit_code=0)
        make_script(fake_bin, "docker-inspect", stdout="true", exit_code=0)
        ins = DockerInspector()
        assert ins.is_running("c") is True

    def test_is_running_false(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="false", exit_code=0)
        make_script(fake_bin, "docker-inspect", stdout="false", exit_code=0)
        ins = DockerInspector()
        assert ins.is_running("c") is False

    def test_is_running_false_when_docker_missing(self) -> None:
        ins = DockerInspector()
        assert ins.is_running("c") is False

    def test_ps(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="CONTAINER  STATUS", exit_code=0)
        ins = DockerInspector()
        result = ins.ps()
        assert result.success is True

    def test_logs(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="[INFO] logs", exit_code=0)
        make_script(fake_bin, "docker-logs", stdout="[INFO] logs", exit_code=0)
        ins = DockerInspector()
        result = ins.logs("c")
        assert result.success is True

    def test_logs_with_follow(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="[INFO] logs", exit_code=0)
        make_script(fake_bin, "docker-logs", stdout="[INFO] logs", exit_code=0)
        ins = DockerInspector()
        result = ins.logs("c", follow=True)
        assert result.success is True

    def test_logs_gracefully_fails_when_docker_missing(self) -> None:
        ins = DockerInspector()
        result = ins.logs("c")
        assert result.success is False

    def test_docker_get_env_found(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="LLAMA_MODEL=m.gguf\nCTX_SIZE=8192", exit_code=0)
        ins = DockerInspector()
        val = ins.get_env("c", "LLAMA_MODEL")
        assert val == "m.gguf"

    def test_docker_get_env_not_found(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="PORT=8080\n", exit_code=0)
        ins = DockerInspector()
        val = ins.get_env("c", "MISSING")
        assert val is None

    def test_docker_get_env_container_missing(self) -> None:
        ins = DockerInspector()
        val = ins.get_env("nonexistent", "LLAMA_MODEL")
        assert val is None


class TestDockerOperator:
    def test_exec(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="out", exit_code=0)
        make_script(fake_bin, "docker-exec", stdout="out", exit_code=0)
        op = DockerOperator()
        result = op.exec("c", "echo", "hi")
        assert result.success is True

    def test_exec_gracefully_fails_when_docker_missing(self) -> None:
        op = DockerOperator()
        result = op.exec("c", "echo", "hi", capture_output=True)
        assert result.success is False

    def test_copy_to(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="", exit_code=0)
        make_script(fake_bin, "docker-cp", stdout="", exit_code=0)
        op = DockerOperator()
        result = op.copy_to("src", "c", "dest")
        assert result.success is True
