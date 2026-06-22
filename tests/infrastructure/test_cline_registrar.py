"""Integration tests for ClineModelRegistrar (fixture files, no real cline config)."""

from __future__ import annotations

import json
from pathlib import Path

from gb_ai_server.infrastructure.persistence import ClineModelRegistrar
from tests.conftest import make_logger_mock


class TestClineModelRegistrar:
    def test_creates_providers_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_models(
            models=[("model-a", "a.gguf", 8081)],
        )

        assert result is True
        providers_file = cline_data / "settings" / "providers.json"
        assert providers_file.exists()
        data = json.loads(providers_file.read_text())
        assert data["version"] == 1
        assert data["lastUsedProvider"] == "local llama"
        provider = data["providers"]["local llama"]
        assert provider["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert provider["settings"]["model"] == "a.gguf"
        assert provider["settings"]["provider"] == "openai-compatible"

    def test_updates_global_state(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        registrar.register_models(
            models=[("model-a", "a.gguf", 8081)],
        )

        state_file = cline_data / "globalState.json"
        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["actModeApiProvider"] == "local llama"
        assert data["planModeApiProvider"] == "local llama"
        assert data["actModeOpenAiModelId"] == "a.gguf"
        assert data["planModeOpenAiModelId"] == "a.gguf"
        assert data["openAiBaseUrl"] == "http://localhost:8081/v1"

    def test_uses_provider_base_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        registrar.register_models(
            models=[("model-a", "a.gguf", 8081)],
            provider_base_url="http://localhost:9999",
        )

        providers_file = cline_data / "settings" / "providers.json"
        data = json.loads(providers_file.read_text())
        assert data["providers"]["local llama"]["settings"]["baseUrl"] == "http://localhost:9999/v1"

    def test_preserves_existing_providers(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        settings_dir = cline_data / "settings"
        settings_dir.mkdir(parents=True, exist_ok=True)
        providers_file = settings_dir / "providers.json"
        providers_file.write_text(
            json.dumps({
                "version": 1,
                "lastUsedProvider": "openrouter",
                "providers": {
                    "openrouter": {
                        "settings": {"provider": "openrouter", "apiKey": "sk-test"},
                        "updatedAt": "2026-01-01T00:00:00",
                        "tokenSource": "manual",
                    }
                },
            })
        )

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_models(
            models=[("model-a", "a.gguf", 8081)],
        )

        data = json.loads(providers_file.read_text())
        assert "openrouter" in data["providers"]
        assert data["providers"]["openrouter"]["settings"]["apiKey"] == "sk-test"
        assert "local llama" in data["providers"]

    def test_returns_false_with_no_models(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_models(models=[])

        assert result is False

    def test_is_registered_checks_state(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_models(
            models=[("model-a", "a.gguf", 8081)],
        )

        assert registrar.is_registered("a.gguf") is True
        assert registrar.is_registered("nonexistent") is False

    def test_first_model_port_as_default_base_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        registrar.register_models(
            models=[("model-a", "a.gguf", 8081), ("model-b", "b.gguf", 8082)],
        )

        providers_file = cline_data / "settings" / "providers.json"
        data = json.loads(providers_file.read_text())
        assert data["providers"]["local llama"]["settings"]["baseUrl"] == "http://localhost:8081/v1"

    def test_uses_CLINE_DATA_DIR_env_var(self, tmp_path: Path, monkeypatch) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "custom-cline"
        monkeypatch.setenv("CLINE_DATA_DIR", str(cline_data))

        registrar = ClineModelRegistrar(logger)
        registrar.register_models(
            models=[("model-a", "a.gguf", 8081)],
        )

        providers_file = cline_data / "settings" / "providers.json"
        assert providers_file.exists()
