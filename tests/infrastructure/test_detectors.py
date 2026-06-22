"""Integration tests for detector classes (fixture scripts, no real tools)."""

from pathlib import Path

import pytest

from gb_ai_server.infrastructure.container_runtime.detector import (
    FallbackRuntimeDetector,
)
from gb_ai_server.infrastructure.compose.detector import FallbackComposeDetector
from gb_ai_server.infrastructure.container_runtime.podman import PodmanRuntime
from gb_ai_server.infrastructure.container_runtime.docker import DockerRuntime
from gb_ai_server.infrastructure.compose.podman_standalone import (
    PodmanComposeStandalone,
)
from gb_ai_server.infrastructure.compose.docker_standalone import (
    DockerComposeStandalone,
)
from tests.helpers import make_script


class TestFallbackRuntimeDetector:
    def test_detect_returns_podman_when_available(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="CONTAINER ID", exit_code=0)
        runtime = FallbackRuntimeDetector().detect()
        assert isinstance(runtime, PodmanRuntime)
        assert runtime.is_available() is True

    def test_detect_returns_docker_when_podman_missing(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="CONTAINER ID", exit_code=0)
        runtime = FallbackRuntimeDetector().detect()
        assert isinstance(runtime, DockerRuntime)
        assert runtime.is_available() is True
    def test_detect_raises_when_no_runtime(self, fake_bin: Path) -> None:
        with pytest.raises(RuntimeError, match="No container runtime found"):
            FallbackRuntimeDetector().detect()



class TestFallbackComposeDetector:
    def test_detect_returns_podman_compose_when_available(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman-compose", stdout="version", exit_code=0)
        tool = FallbackComposeDetector().detect()
        assert isinstance(tool, PodmanComposeStandalone)

    def test_detect_returns_docker_compose_when_podman_missing(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker-compose", stdout="version", exit_code=0)
        tool = FallbackComposeDetector().detect()
        assert isinstance(tool, DockerComposeStandalone)

    def test_detect_raises_when_no_compose_tool(self, fake_bin: Path) -> None:
        with pytest.raises(RuntimeError, match="No compose tool found"):
            FallbackComposeDetector().detect()
