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

        result = registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
        )

        assert result is True
        providers_file = cline_data / "settings" / "providers.json"
        assert providers_file.exists()
        data = json.loads(providers_file.read_text())
        assert data["version"] == 1
        assert data["lastUsedProvider"] == "openai-compatible"
        provider = data["providers"]["openai-compatible"]
        assert provider["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert provider["settings"]["model"] == "a.gguf"
        assert provider["settings"]["provider"] == "openai-compatible"
        
        # Check custom container provider is also written
        assert "llama-coder" in data["providers"]

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
        registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
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

    def test_sets_active_provider_to_openai_compatible(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        cline_data.mkdir(parents=True, exist_ok=True)
        state_file = cline_data / "globalState.json"
        state_file.write_text(
            json.dumps({
                "apiProvider": "local-llama",
                "actModeApiProvider": "local-llama",
            })
        )

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
        )

        data = json.loads(state_file.read_text())
        # The active provider must be updated to openai-compatible
        assert data["apiProvider"] == "openai-compatible"
        assert data["actModeApiProvider"] == "openai-compatible"
        assert data["openAiModelId"] == "a.gguf"
        assert data["openAiBaseUrl"] == "http://localhost:8081/v1"

    def test_uses_provider_base_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
            provider_base_url="http://localhost:9999",
        )

        providers_file = cline_data / "settings" / "providers.json"
        data = json.loads(providers_file.read_text())
        assert data["providers"]["openai-compatible"]["settings"]["baseUrl"] == "http://localhost:9999/v1"

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
        registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
        )

        data = json.loads(providers_file.read_text())
        assert "openrouter" in data["providers"]
        assert data["providers"]["openrouter"]["settings"]["apiKey"] == "sk-test"
        assert "openai-compatible" in data["providers"]

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
        registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
        )

        data = json.loads(providers_file.read_text())
        assert data["providers"]["openai-compatible"]["settings"]["apiKey"] == "sk-external-key"
        assert data["providers"]["openai-compatible"]["settings"]["baseUrl"] == "https://api.together.xyz/v1"

    def test_overwrites_default_openai_compatible_provider(self, tmp_path: Path) -> None:
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
                            "baseUrl": "https://api.openai.com/v1",
                            "apiKey": "some-key"
                        }
                    }
                },
            })
        )

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
        )

        data = json.loads(providers_file.read_text())
        assert data["providers"]["openai-compatible"]["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert data["providers"]["openai-compatible"]["settings"]["apiKey"] == "dummy"

    def test_returns_false_with_no_models(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_model(model=None)  # type: ignore[arg-type]

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

        registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
        )

        providers_file = cline_data / "settings" / "providers.json"
        data = json.loads(providers_file.read_text())
        assert data["providers"]["openai-compatible"]["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert data["providers"]["openai-compatible"]["settings"]["model"] == "a.gguf"
        assert "llama-coder" in data["providers"]

    def test_uses_CLINE_DATA_DIR_env_var(self, tmp_path: Path, monkeypatch) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "custom-cline"
        monkeypatch.setenv("CLINE_DATA_DIR", str(cline_data))

        registrar = ClineModelRegistrar(logger)
        registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
        )

        providers_file = cline_data / "settings" / "providers.json"
        assert providers_file.exists()

    def test_creates_models_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_model(
            model=("model-a", "a.gguf", 8081, "llama-coder"),
        )

        assert result is True
        models_file = cline_data / "settings" / "models.json"
        assert models_file.exists()
        data = json.loads(models_file.read_text())
        
        # Check custom container providers are written
        assert "llama-coder" in data["providers"]
        assert data["providers"]["llama-coder"]["provider"]["defaultModelId"] == "a.gguf"
        assert "a.gguf" in data["providers"]["llama-coder"]["models"]

        assert "openai-compatible" in data["providers"]
        # defaultModelId is non-prefixed (like ollama provider)
        assert data["providers"]["openai-compatible"]["provider"]["defaultModelId"] == "a.gguf"
        # models dict keys are non-prefixed
        assert "a.gguf" in data["providers"]["openai-compatible"]["models"]
        # a.gguf doesn't match any model size pattern → mapper returns default context_size=4096
        assert data["providers"]["openai-compatible"]["models"]["a.gguf"]["contextWindow"] == 4096
        assert "tools" in data["providers"]["openai-compatible"]["models"]["a.gguf"]["capabilities"]
        # Check modelsSourceUrl is set
        assert data["providers"]["openai-compatible"]["provider"]["modelsSourceUrl"] == "http://localhost:8081/models"
        assert data["providers"]["openai-compatible"]["provider"]["protocol"] == "openai-chat"
        assert data["providers"]["openai-compatible"]["provider"]["client"] == "openai-compatible"

    def test_registers_context_window_from_filename(self, tmp_path: Path) -> None:
        """Context window is derived from filename via ResourceRequirementsMapper."""
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_model(
            model=("qwen2.5-coder:7b", "qwen2.5-coder-7b-instruct-q4_k_m.gguf", 8081, "llama-coder"),
        )

        assert result is True
        models_file = cline_data / "settings" / "models.json"
        data = json.loads(models_file.read_text())
        # 7b pattern → context_size=8192 from the mapper
        assert data["providers"]["openai-compatible"]["models"]["qwen2.5-coder-7b-instruct-q4_k_m.gguf"]["contextWindow"] == 8192
        assert data["providers"]["openai-compatible"]["models"]["qwen2.5-coder-7b-instruct-q4_k_m.gguf"]["maxInputTokens"] == 8192
