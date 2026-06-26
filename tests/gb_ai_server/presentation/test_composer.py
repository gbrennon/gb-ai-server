"""Tests for presentation layer BootstrapCompositionRoot."""

from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gb_ai_server.domain import CommandResult, ModelEntry
from gb_ai_server.presentation.composer import BootstrapCompositionRoot


def _default_args(**overrides) -> Namespace:
    base = {
        "dry_run": False,
        "skip_download": False,
        "skip_health": False,
        "models_dir": Path("/tmp/models"),
        "hf_token": None,
        "debug": False,
        "model": None,
    }
    base.update(overrides)
    return Namespace(**base)


@pytest.fixture
def mock_env() -> MagicMock:
    env = MagicMock()
    env.paths.compose_file = Path("/tmp/compose.yml")
    env.paths.models_config_path = Path("/tmp/models.conf.sh")
    env.debug = False
    return env


@pytest.fixture(autouse=True)
def mock_cline_registrar() -> MagicMock:
    with patch("gb_ai_server.presentation.composer.ClineModelRegistrar") as mock:
        yield mock


@pytest.fixture
def mock_models() -> list[ModelEntry]:
    return [ModelEntry("qwen:7b", "qwen.gguf", "https://example.com/q")]


def _make_mock_service(execute_result: CommandResult | None = None) -> MagicMock:
    svc = MagicMock()
    if execute_result is not None:
        svc.execute.return_value = execute_result
    else:
        response = MagicMock()
        response.results = {"all": True}
        svc.execute.return_value = response
    return svc


def _make_mock_service_with_response(results: dict) -> MagicMock:
    svc = MagicMock()
    response = MagicMock()
    response.results = results
    svc.execute.return_value = response
    return svc


def _make_mock_container(
    verifier_result: CommandResult | None = None,
    start_result: CommandResult | None = None,
    restart_result: CommandResult | None = None,
    health_result: CommandResult | None = None,
    verifier_has_tools: bool = True,
) -> MagicMock:
    container = MagicMock()
    container.logger = MagicMock()

    result = verifier_result if verifier_result is not None else MagicMock()
    if verifier_result is None:
        result.success = True

    if verifier_has_tools:
        result.compose_tool = MagicMock()
        result.container_runtime = MagicMock()
        result.container_runtime.is_running.return_value = False
        result.inspector = MagicMock()
        result.operator = MagicMock()
        result.compose_lifecycle = MagicMock()
        result.compose_query = MagicMock()
    else:
        result.compose_tool = None
        result.container_runtime = None
        result.inspector = None
        result.operator = None
        result.compose_lifecycle = None
        result.compose_query = None

    verifier = MagicMock()
    verifier.execute.return_value = result
    container.prerequisite_verifier.return_value = verifier

    container.start_services.return_value = _make_mock_service(
        start_result if start_result is not None else None
    )
    container.stop_services.return_value = _make_mock_service(None)
    container.restart_services.return_value = _make_mock_service(
        restart_result if restart_result is not None else None
    )
    container.health_verifier.return_value = _make_mock_service(
        health_result if health_result is not None else None
    )
    container.model_downloader.return_value = _make_mock_service_with_response(
        {"test": True}
    )
    container.model_copier.return_value = _make_mock_service_with_response(
        {"test": True}
    )
    container.model_registrar.return_value = _make_mock_service()

    return container


class TestBootstrapCompositionRoot:
    def test_happy_path_returns_zero(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args()
        container = _make_mock_container()

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 0

    def test_returns_one_when_no_models(
        self, mock_env: MagicMock
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container()

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                side_effect=SystemExit(1),
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 1

    def test_returns_one_when_prerequisites_fail(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container(
            verifier_result=CommandResult(
                returncode=1, stdout="", stderr="fail", success=False
            )
        )

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 1

    def test_returns_one_when_detection_fails(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container(verifier_has_tools=False)

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 1

    def test_skip_download_skips_download_step(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container()

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 0
                container.model_downloader.assert_not_called()

    def test_skip_health_skips_health_step(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container()

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 0
                container.health_verifier.assert_not_called()

    def test_returns_one_when_start_fails(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container(
            start_result=CommandResult(
                returncode=1, stdout="", stderr="fail", success=False
            )
        )

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 1

    def test_returns_one_when_restart_fails(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container(
            restart_result=CommandResult(
                returncode=1, stdout="", stderr="fail", success=False
            )
        )

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 1

    def test_returns_one_when_health_fails(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=False)
        container = _make_mock_container(
            health_result=CommandResult(
                returncode=1, stdout="", stderr="fail", success=False
            )
        )

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 1

    def test_start_services_uses_service_name_llama(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container()

        with (
            patch.object(
                BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
            ),
            patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ),
        ):
            root = BootstrapCompositionRoot(container)
            root.run(args)

        execute_call = container.start_services.return_value.execute
        execute_call.assert_called_once()
        request = execute_call.call_args[0][0]
        assert request.compose_file == str(mock_env.paths.compose_file)
        assert request.services == ("llama",)

    def test_restart_services_uses_service_name_llama(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container()

        with (
            patch.object(
                BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
            ),
            patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ),
        ):
            root = BootstrapCompositionRoot(container)
            root.run(args)

        execute_call = container.restart_services.return_value.execute
        execute_call.assert_called_once()
        request = execute_call.call_args[0][0]
        assert request.compose_file == str(mock_env.paths.compose_file)
        assert request.services == ("llama",)

    def test_when_model_already_running_registers_and_returns_zero(
        self, mock_env: MagicMock, mock_models: list[ModelEntry]
    ) -> None:
        args = _default_args()
        container = _make_mock_container()

        # Mock that the model is already running by returning the filename
        # from inspector.get_env
        verifier_execute_result = container.prerequisite_verifier.return_value.execute.return_value
        verifier_execute_result.inspector.is_running.return_value = True
        verifier_execute_result.inspector.get_env.return_value = mock_models[0].filename

        with (
            patch.object(
                BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
            ),
            patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                return_value=mock_models,
            ),
            patch("gb_ai_server.presentation.composer.Path.exists", return_value=True),
        ):
            root = BootstrapCompositionRoot(container)
            assert root.run(args) == 0

        # Verify that model registrar was executed anyway
        container.model_registrar.return_value.execute.assert_called_once()

    def test_catches_unexpected_exception(self, mock_env: MagicMock) -> None:
        args = _default_args(skip_download=True, skip_health=True)
        container = _make_mock_container()

        with patch.object(
            BootstrapCompositionRoot, "_setup_environment", return_value=mock_env
        ):
            with patch.object(
                BootstrapCompositionRoot,
                "_load_models_config",
                side_effect=RuntimeError("unexpected"),
            ):
                root = BootstrapCompositionRoot(container)
                assert root.run(args) == 1
                container.logger.error.assert_called_once()
