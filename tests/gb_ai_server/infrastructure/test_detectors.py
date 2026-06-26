"""Integration tests for detector classes (fixture scripts, no real tools)."""

from pathlib import Path

import pytest

from gb_ai_server.infrastructure.container_runtime.detector import (
    FallbackRuntimeDetector,
)
from gb_ai_server.infrastructure.container_runtime.podman_runtime import PodmanRuntime
from gb_ai_server.infrastructure.container_runtime.podman_inspector import PodmanInspector
from gb_ai_server.infrastructure.container_runtime.podman_operator import PodmanOperator
from gb_ai_server.infrastructure.container_runtime.docker_runtime import DockerRuntime
from gb_ai_server.infrastructure.container_runtime.docker_inspector import DockerInspector
from gb_ai_server.infrastructure.container_runtime.docker_operator import DockerOperator

from gb_ai_server.infrastructure.compose.podman_standalone_lifecycle import PodmanComposeStandaloneLifecycle
from gb_ai_server.infrastructure.compose.podman_standalone_query import PodmanComposeStandaloneQuery
from gb_ai_server.infrastructure.compose.podman_builtin_lifecycle import PodmanComposeBuiltinLifecycle
from gb_ai_server.infrastructure.compose.podman_builtin_query import PodmanComposeBuiltinQuery
from gb_ai_server.infrastructure.compose.docker_standalone_lifecycle import DockerComposeStandaloneLifecycle
from gb_ai_server.infrastructure.compose.docker_standalone_query import DockerComposeStandaloneQuery
from gb_ai_server.infrastructure.compose.docker_builtin_lifecycle import DockerComposeBuiltinLifecycle
from gb_ai_server.infrastructure.compose.docker_builtin_query import DockerComposeBuiltinQuery
from gb_ai_server.infrastructure.compose.detector import FallbackComposeDetector
from gb_ai_server.infrastructure.compose.podman_standalone_runtime import (
    PodmanComposeStandalone,
)
from gb_ai_server.infrastructure.compose.docker_standalone_runtime import (
    DockerComposeStandalone,
)
from gb_ai_server.infrastructure.compose.podman_builtin_runtime import PodmanComposeBuiltin
from gb_ai_server.infrastructure.compose.docker_builtin_runtime import DockerComposeBuiltin
from tests.gb_ai_server.helpers import make_script


class TestFallbackRuntimeDetector:
    def test_detect_returns_podman_when_available(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="CONTAINER ID", exit_code=0)
        detection = FallbackRuntimeDetector().detect()
        assert isinstance(detection.runtime, PodmanRuntime)
        assert isinstance(detection.inspector, PodmanInspector)
        assert isinstance(detection.operator, PodmanOperator)
        assert detection.runtime.is_available() is True

    def test_detect_returns_docker_when_podman_missing(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="CONTAINER ID", exit_code=0)
        detection = FallbackRuntimeDetector().detect()
        assert isinstance(detection.runtime, DockerRuntime)
        assert isinstance(detection.inspector, DockerInspector)
        assert isinstance(detection.operator, DockerOperator)
        assert detection.runtime.is_available() is True

    def test_detect_raises_when_no_runtime(self, fake_bin: Path) -> None:
        with pytest.raises(RuntimeError, match="No container runtime found"):
            FallbackRuntimeDetector().detect()



class TestFallbackComposeDetector:
    def test_detect_returns_podman_compose_when_available(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman-compose", stdout="version", exit_code=0)
        detection = FallbackComposeDetector().detect()
        assert isinstance(detection.tool, PodmanComposeStandalone)
        assert isinstance(detection.lifecycle, PodmanComposeStandaloneLifecycle)
        assert isinstance(detection.query, PodmanComposeStandaloneQuery)

    def test_detect_returns_docker_compose_when_podman_missing(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker-compose", stdout="version", exit_code=0)
        detection = FallbackComposeDetector().detect()
        assert isinstance(detection.tool, DockerComposeStandalone)
        assert isinstance(detection.lifecycle, DockerComposeStandaloneLifecycle)
        assert isinstance(detection.query, DockerComposeStandaloneQuery)

    def test_detect_raises_when_no_compose_tool(self, fake_bin: Path) -> None:
        with pytest.raises(RuntimeError, match="No compose tool found"):
            FallbackComposeDetector().detect()

    def test_detect_returns_podman_builtin_when_only_running_podman(self, fake_bin: Path) -> None:
        make_script(fake_bin, "podman", stdout="docker compose version", exit_code=0)
        detection = FallbackComposeDetector().detect()
        assert isinstance(detection.tool, PodmanComposeBuiltin)
        assert isinstance(detection.lifecycle, PodmanComposeBuiltinLifecycle)
        assert isinstance(detection.query, PodmanComposeBuiltinQuery)

    def test_detect_returns_docker_builtin_when_only_running_docker(self, fake_bin: Path) -> None:
        make_script(fake_bin, "docker", stdout="docker compose version", exit_code=0)
        detection = FallbackComposeDetector().detect()
        assert isinstance(detection.tool, DockerComposeBuiltin)
        assert isinstance(detection.lifecycle, DockerComposeBuiltinLifecycle)
        assert isinstance(detection.query, DockerComposeBuiltinQuery)
