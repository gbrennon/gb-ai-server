"""Integration tests for Podman runtime/inspector/operator adapters."""

from pathlib import Path

from gb_ai_server.infrastructure.executors.podman import PodmanRuntime
from gb_ai_server.infrastructure.executors.podman import PodmanInspector
from gb_ai_server.infrastructure.executors.podman import PodmanOperator
from tests.gb_ai_server.helpers import make_script


class TestPodmanRuntime:
    def test_name(self) -> None:
        rt = PodmanRuntime()
        assert rt.name == "podman"

    def test_pretty_name(self) -> None:
        rt = PodmanRuntime()
        assert rt.pretty_name == "Podman"

    def test_is_available_when_podman_works(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="CONTAINER ID", exit_code=0)
        rt = PodmanRuntime()
        assert rt.is_available() is True

    def test_is_available_false_when_podman_fails(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="", exit_code=1)
        rt = PodmanRuntime()
        assert rt.is_available() is False


class TestPodmanInspector:
    def test_is_running_true(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="true", exit_code=0)
        make_script(fake_bin, "podman-inspect", stdout="true", exit_code=0)
        ins = PodmanInspector()
        assert ins.is_running("test-container") is True

    def test_is_running_false(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="false", exit_code=0)
        make_script(fake_bin, "podman-inspect", stdout="false", exit_code=0)
        ins = PodmanInspector()
        assert ins.is_running("test-container") is False

    def test_ps(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="CONTAINER  IMAGE  STATUS", exit_code=0)
        ins = PodmanInspector()
        result = ins.ps()
        assert result.success is True
        assert "CONTAINER" in result.stdout

    def test_logs(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="[INFO] log line", exit_code=0)
        make_script(fake_bin, "podman-logs", stdout="[INFO] log line", exit_code=0)
        ins = PodmanInspector()
        result = ins.logs("c")
        assert result.success is True
        assert "log" in result.stdout

    def test_logs_with_follow(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="[INFO] log line", exit_code=0)
        make_script(fake_bin, "podman-logs", stdout="[INFO] log line", exit_code=0)
        ins = PodmanInspector()
        result = ins.logs("c", follow=True)
        assert result.success is True

    def test_get_env_found(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="LLAMA_MODEL=my-model.gguf\nPORT=8080", exit_code=0)
        ins = PodmanInspector()
        val = ins.get_env("c", "LLAMA_MODEL")
        assert val == "my-model.gguf"

    def test_get_env_not_found(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="PORT=8080\n", exit_code=0)
        ins = PodmanInspector()
        val = ins.get_env("c", "OTHER_VAR")
        assert val is None

    def test_get_env_container_missing(self) -> None:
        ins = PodmanInspector()
        val = ins.get_env("nonexistent", "LLAMA_MODEL")
        assert val is None


class TestPodmanOperator:
    def test_exec(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="exec result", exit_code=0)
        op = PodmanOperator()
        result = op.exec("c", "echo", "hi", capture_output=True)
        assert result.success is True
        assert "exec" in result.stdout

    def test_exec_with_capture_output(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="captured", exit_code=0)
        make_script(fake_bin, "podman-exec", stdout="captured", exit_code=0)
        op = PodmanOperator()
        result = op.exec("c", "echo", "hi", capture_output=True)
        assert result.success is True

    def test_copy_to(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="", exit_code=0)
        make_script(fake_bin, "podman-cp", stdout="", exit_code=0)
        op = PodmanOperator()
        result = op.copy_to(Path("/src/file"), "c", "/dest/file")
        assert result.success is True
