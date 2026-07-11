"""Integration tests for ClineModelRegistrar (fixture files, no real cline config)."""

from __future__ import annotations

import json
from pathlib import Path

from gb_ai_server.infrastructure.persistence import ClineModelRegistrar
from tests.gb_ai_server.conftest import make_logger_mock


class TestClineModelRegistrar:
    MODEL = ("model-a", "a.gguf", 8081, "llama-coder")

    def test_creates_providers_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_model(model=self.MODEL)

        assert result is True
        providers_file = cline_data / "settings" / "providers.json"
        assert providers_file.exists()
        data = json.loads(providers_file.read_text())
        assert data["version"] == 1
        assert data["lastUsedProvider"] == "openai-compatible"
        provider = data["providers"]["openai-compatible"]
        assert provider["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert provider["settings"]["model"] == "llama-coder"
        assert provider["settings"]["provider"] == "openai-compatible"

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
        registrar.register_model(model=self.MODEL)

        data = json.loads(state_file.read_text())
        assert data["apiProvider"] == "openai-compatible"
        assert data["actModeApiProvider"] == "openai-compatible"
        assert data["openAiModelId"] == "llama-coder"
        assert data["openAiBaseUrl"] == "http://localhost:8081/v1"

    def test_uses_provider_base_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        registrar.register_model(
            model=self.MODEL,
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
        registrar.register_model(model=self.MODEL)

        data = json.loads(providers_file.read_text())
        assert "openrouter" in data["providers"]
        assert data["providers"]["openrouter"]["settings"]["apiKey"] == "sk-test"
        assert "openai-compatible" in data["providers"]

    def test_overwrites_openai_compatible_base_url(self, tmp_path: Path) -> None:
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
        registrar.register_model(model=self.MODEL)

        data = json.loads(providers_file.read_text())
        assert data["providers"]["openai-compatible"]["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert data["providers"]["openai-compatible"]["settings"]["apiKey"] == "sk-external-key"

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
                "apiProvider": "openai-compatible",
                "openAiModelId": "llama-coder",
            })
        )

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        assert registrar.is_registered("llama-coder") is True
        assert registrar.is_registered("nonexistent") is False

    def test_first_model_port_as_default_base_url(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        registrar.register_model(model=self.MODEL)

        providers_file = cline_data / "settings" / "providers.json"
        data = json.loads(providers_file.read_text())
        assert data["providers"]["openai-compatible"]["settings"]["baseUrl"] == "http://localhost:8081/v1"
        assert data["providers"]["openai-compatible"]["settings"]["model"] == "llama-coder"
        assert "openai-compatible" in data["providers"]

    def test_uses_CLINE_DATA_DIR_env_var(self, tmp_path: Path, monkeypatch) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "custom-cline"
        monkeypatch.setenv("CLINE_DATA_DIR", str(cline_data))

        registrar = ClineModelRegistrar(logger)
        registrar.register_model(model=self.MODEL)

        providers_file = cline_data / "settings" / "providers.json"
        assert providers_file.exists()

    def test_creates_models_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)

        result = registrar.register_model(model=self.MODEL)

        assert result is True
        models_file = cline_data / "settings" / "models.json"
        assert models_file.exists()
        data = json.loads(models_file.read_text())

        assert "openai-compatible" in data["providers"]
        prov = data["providers"]["openai-compatible"]
        assert prov["provider"]["defaultModelId"] == "llama-coder"
        models = prov["models"]
        assert isinstance(models, list)
        assert models[0]["id"] == "llama-coder"
        assert models[0]["name"] == "model-a"

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
        models = data["providers"]["openai-compatible"]["models"]
        model = next(m for m in models if m["id"] == "llama-coder")
        assert model["contextWindow"] in (8192, 131072)
        assert model["maxInputTokens"] in (8192, 131072)

    def test_uses_api_key_from_env_var(self, tmp_path: Path, monkeypatch) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        monkeypatch.setenv("OPENAI_API_KEY", "from-env")

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_model(model=self.MODEL)

        secrets_file = cline_data / "secrets.json"
        data = json.loads(secrets_file.read_text())
        assert data["openAiApiKey"] == "from-env"

    def test_api_key_param_overrides_env(self, tmp_path: Path, monkeypatch) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        monkeypatch.setenv("OPENAI_API_KEY", "from-env")

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data, api_key="explicit")
        registrar.register_model(model=self.MODEL)

        secrets_file = cline_data / "secrets.json"
        data = json.loads(secrets_file.read_text())
        assert data["openAiApiKey"] == "explicit"

    def test_uses_dummy_when_no_api_key_set(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"

        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data)
        registrar.register_model(model=self.MODEL)

        secrets_file = cline_data / "secrets.json"
        data = json.loads(secrets_file.read_text())
        assert data["openAiApiKey"] == "dummy"

    def test_writes_secrets_file(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data, api_key="test-key")

        registrar.register_model(model=self.MODEL)

        secrets_file = cline_data / "secrets.json"
        assert secrets_file.exists()
        data = json.loads(secrets_file.read_text())
        assert data["openAiApiKey"] == "test-key"

    def test_writes_global_state_keys(self, tmp_path: Path) -> None:
        logger = make_logger_mock()
        cline_data = tmp_path / "cline" / "data"
        registrar = ClineModelRegistrar(logger, cline_data_dir=cline_data, api_key="test-key")

        registrar.register_model(model=self.MODEL)

        state_file = cline_data / "globalState.json"
        data = json.loads(state_file.read_text())

        assert data["apiProvider"] == "openai-compatible"
        assert data["openAiModelId"] == "llama-coder"
        assert data["openAiBaseUrl"] == "http://localhost:8081/v1"
        assert data["openAiApiKey"] == "test-key"

        assert data["openai-compatible-model-id"] == "llama-coder"
        assert data["openAiCompatibleModelId"] == "llama-coder"
        assert data["llama-coder-model-id"] == "llama-coder"
        assert data["llamaCoderModelId"] == "llama-coder"
