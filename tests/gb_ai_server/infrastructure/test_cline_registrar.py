"""Integration tests for ClineModelRegistrar (fixture files, no real cline config)."""

from __future__ import annotations

import json
from pathlib import Path

from gb_ai_server.infrastructure.persistence import ClineModelRegistrar
from tests.gb_ai_server.conftest import make_logger_mock


class TestClineModelRegistrar:
    def test_creates_providers_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_models(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
        )

        assert result is True
        providers_file = cline_data / "settings" / "providers.json"
        assert providers_file.exists()
        data = json.loads(providers_file.read_text())
        assert data["version"] == 1
        assert data["lastUsedProvider"] == "llama-coder"
        provider = data["providers"]["llama-coder"]
        assert provider["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert provider["settings"]["model"] == "a.gguf"
        assert provider["settings"]["provider"] == "openai-compatible"
        assert "openai-compatible" in data["providers"]
        assert data["providers"]["openai-compatible"]["settings"]["baseUrl"] == "http://localhost:8081/v1"

    def test_updates_global_state_without_overwriting_provider(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        cline_data.mkdir(parents=True, exist_ok=True)
        state_file = cline_data / "globalState.json"
        state_file.write_text(
            json.dumps({
                "apiProvider": "cline",
                "actModeApiProvider": "cline",
            })
        )

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_models(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
        )

        data = json.loads(state_file.read_text())
        # The active provider must NOT be changed to llama-coder
        assert data["apiProvider"] == "cline"
        assert data["actModeApiProvider"] == "cline"

        # The model ID keys for llama-coder and openai-compatible MUST be set
        assert data["llamaCoderModelId"] == "a.gguf"
        assert data["actModeLlamaCoderModelId"] == "a.gguf"
        assert data["planModeLlamaCoderModelId"] == "a.gguf"
        assert data["openAiCompatibleModelId"] == "a.gguf"
        assert data["actModeOpenAiCompatibleModelId"] == "a.gguf"
        assert data["planModeOpenAiCompatibleModelId"] == "a.gguf"

    def test_migrates_active_provider_from_llama_coder(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        cline_data.mkdir(parents=True, exist_ok=True)
        state_file = cline_data / "globalState.json"
        state_file.write_text(
            json.dumps({
                "apiProvider": "llama-coder",
                "actModeApiProvider": "llama-coder",
            })
        )

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_models(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
        )

        data = json.loads(state_file.read_text())
        # The active provider must be migrated to openai-compatible
        assert data["apiProvider"] == "openai-compatible"
        assert data["actModeApiProvider"] == "openai-compatible"
        assert data["openAiModelId"] == "a.gguf"
        assert data["openAiBaseUrl"] == "http://localhost:8081/v1"

    def test_uses_provider_base_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        registrar.register_models(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
            provider_base_url="http://localhost:9999",
        )

        providers_file = cline_data / "settings" / "providers.json"
        data = json.loads(providers_file.read_text())
        assert data["providers"]["llama-coder"]["settings"]["baseUrl"] == "http://localhost:9999/v1"

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
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
        )

        data = json.loads(providers_file.read_text())
        assert "openrouter" in data["providers"]
        assert data["providers"]["openrouter"]["settings"]["apiKey"] == "sk-test"
        assert "llama-coder" in data["providers"]

    def test_preserves_external_openai_compatible_provider(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        settings_dir = cline_data / "settings"
        settings_dir.mkdir(parents=True, exist_ok=True)
        providers_file = settings_dir / "providers.json"
        providers_file.write_text(
            json.dumps({
                "version": 1,
                "providers": {
                    "openai-compatible": {
                        "settings": {
                            "provider": "openai-compatible",
                            "baseUrl": "https://api.together.xyz/v1",
                            "apiKey": "sk-external-key"
                        }
                    }
                },
            })
        )

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_models(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
        )

        data = json.loads(providers_file.read_text())
        assert data["providers"]["openai-compatible"]["settings"]["apiKey"] == "sk-external-key"
        assert data["providers"]["openai-compatible"]["settings"]["baseUrl"] == "https://api.together.xyz/v1"

    def test_returns_false_with_no_models(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_models(models=[])

        assert result is False

    def test_is_registered_checks_state(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        cline_data.mkdir(parents=True, exist_ok=True)
        state_file = cline_data / "globalState.json"
        state_file.write_text(
            json.dumps({
                "apiProvider": "llama-coder",
                "openAiModelId": "a.gguf"
            })
        )

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        # is_registered accepts both provider-prefixed and non-prefixed model names
        assert registrar.is_registered("a.gguf") is True
        assert registrar.is_registered("llama-coder/a.gguf") is True
        assert registrar.is_registered("nonexistent") is False

    def test_first_model_port_as_default_base_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        registrar.register_models(
            models=[("model-a", "a.gguf", 8081, "llama-coder"), ("model-b", "b.gguf", 8082, "llama-qwen3")],
        )

        providers_file = cline_data / "settings" / "providers.json"
        data = json.loads(providers_file.read_text())
        assert data["providers"]["llama-coder"]["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert data["providers"]["llama-coder"]["settings"]["model"] == "a.gguf"
        assert data["providers"]["llama-qwen3"]["settings"]["baseUrl"] == "http://localhost:8082/v1"
        assert data["providers"]["llama-qwen3"]["settings"]["model"] == "b.gguf"
        assert data["providers"]["llama-qwen3"]["settings"]["provider"] == "openai-compatible"
        assert "openai-compatible" in data["providers"]
        assert "openai-native" in data["providers"]

    def test_uses_CLINE_DATA_DIR_env_var(self, tmp_path: Path, monkeypatch) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "custom-cline"
        monkeypatch.setenv("CLINE_DATA_DIR", str(cline_data))

        registrar = ClineModelRegistrar(logger)
        registrar.register_models(
            models=[("model-a", "a.gguf", 8081, "llama-coder")],
        )

        providers_file = cline_data / "settings" / "providers.json"
        assert providers_file.exists()

    def test_creates_models_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_models(
            models=[("model-a", "a.gguf", 8081, "llama-coder"), ("model-b", "b.gguf", 8082, "llama-qwen3")],
        )

        assert result is True
        models_file = cline_data / "settings" / "models.json"
        assert models_file.exists()
        data = json.loads(models_file.read_text())
        assert "llama-coder" in data["providers"]
        # defaultModelId is non-prefixed (like ollama provider)
        assert data["providers"]["llama-coder"]["provider"]["defaultModelId"] == "a.gguf"
        # models dict keys are non-prefixed
        assert "a.gguf" in data["providers"]["llama-coder"]["models"]
        assert data["providers"]["llama-coder"]["models"]["a.gguf"]["contextWindow"] == 8192
        assert "tools" in data["providers"]["llama-coder"]["models"]["a.gguf"]["capabilities"]
        # Check modelsSourceUrl is set
        assert data["providers"]["llama-coder"]["provider"]["modelsSourceUrl"] == "http://localhost:8081/models"
        assert data["providers"]["llama-coder"]["provider"]["protocol"] == "openai-chat"
        assert data["providers"]["llama-coder"]["provider"]["client"] == "openai-compatible"
        assert "llama-qwen3" in data["providers"]
        assert data["providers"]["llama-qwen3"]["provider"]["defaultModelId"] == "b.gguf"
        assert "b.gguf" in data["providers"]["llama-qwen3"]["models"]
        assert data["providers"]["llama-qwen3"]["models"]["b.gguf"]["contextWindow"] == 8192
        assert data["providers"]["llama-qwen3"]["provider"]["modelsSourceUrl"] == "http://localhost:8082/models"
        assert "openai-compatible" in data["providers"]
        assert "openai-native" in data["providers"]
