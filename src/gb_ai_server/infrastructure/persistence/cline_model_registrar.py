"""Cline model registrar - registers local models with Cline."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ...application.ports.outbound.logger import Logger


def _resolve_ctx_size(filename: str) -> int:
    """Resolve context window from GGUF metadata or fall back to default.

    Tries GGUF metadata first, then falls back to 32768 (safe default).
    """
    from gb_ai_server.infrastructure.persistence.gguf_reader import read_context_window
    import os

    search_dirs = os.environ.get("MODEL_DIRS", os.environ.get("MODELS_DIR", "")).split(":")
    search_dirs = [d for d in search_dirs if d]
    search_dirs.append(os.getcwd())

    for base in search_dirs:
        candidate = os.path.join(base, filename)
        if os.path.exists(candidate):
            ctx = read_context_window(candidate)
            if ctx:
                return ctx

    return 32768

class ClineModelRegistrar:
    """Register local models with Cline by updating ~/.cline/ configuration.

    Writes to:
      - ~/.cline/data/settings/providers.json  — provider entries with base URLs
      - ~/.cline/data/settings/models.json     — provider models catalog
      - ~/.cline/data/globalState.json          — provider model mappings
      - ~/.cline/data/secrets.json              — API keys
    """

    PROVIDER_ID = "openai-compatible"

    def __init__(
        self,
        logger: Logger,
        cline_data_dir: str | Path | None = None,
        api_key: str | None = None,
    ) -> None:
        self.logger = logger
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "dummy")
        cline_home = (
            Path(cline_data_dir)
            if cline_data_dir
            else Path(os.environ.get("CLINE_DATA_DIR", Path.home() / ".cline" / "data"))
        )
        self._settings_dir = cline_home / "settings"
        self._settings_dir.mkdir(parents=True, exist_ok=True)
        self._providers_file = self._settings_dir / "providers.json"
        self._models_file = self._settings_dir / "models.json"
        self._state_file = cline_home / "globalState.json"
        self._secrets_file = cline_home / "secrets.json"

    def register_model(
        self,
        model: tuple[str, str, int, str],
        provider_base_url: str | None = None,
    ) -> bool:
        if model is None:
            self.logger.warn("No model to register with Cline")
            return False

        try:
            self._update_providers(model, provider_base_url)
            self._update_models(model, provider_base_url)
            self._update_global_state(model)
            self._update_secrets()

            self.logger.ok("Registered model with Cline")
            return True
        except Exception as e:
            self.logger.warn(f"Failed to register model with Cline: {e}")
            return False

    def is_registered(self, model_name: str) -> bool:
        if not self._state_file.exists():
            return False
        try:
            data = json.loads(self._state_file.read_text())
            provider = (
                data.get("actModeApiProvider")
                or data.get("act-mode-api-provider")
                or data.get("apiProvider")
                or data.get("api-provider")
            )
            model_id = (
                data.get("actModeOpenAiModelId")
                or data.get("act-mode-open-ai-model-id")
                or data.get("openAiModelId")
                or data.get("open-ai-model-id")
            )
            if model_id == model_name:
                return True
            if provider == self.PROVIDER_ID and model_id == model_name:
                return True
            return provider is not None and model_id == model_name
        except Exception:
            return False

    def _update_providers(
        self,
        model: tuple[str, str, int, str],
        provider_base_url: str | None = None,
    ) -> None:
        data: dict = {}
        if self._providers_file.exists():
            try:
                data = json.loads(self._providers_file.read_text())
            except json.JSONDecodeError:
                data = {}

        if "version" not in data:
            data["version"] = 1
        if "providers" not in data:
            data["providers"] = {}

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        display_name, filename, port, container_name = model[0], model[1], model[2], model[3]
        base_url = provider_base_url or f"http://localhost:{port}"

        data["lastUsedProvider"] = self.PROVIDER_ID

        existing_settings = (
            data["providers"].get(self.PROVIDER_ID, {}).get("settings", {})
        )

        data["providers"][self.PROVIDER_ID] = {
            "settings": {
                "provider": self.PROVIDER_ID,
                "apiKey": existing_settings.get("apiKey", self._api_key),
                "model": container_name,
                "baseUrl": f"{base_url}/v1",
                "timeout": existing_settings.get("timeout", 30000),
                "reasoning": existing_settings.get("reasoning", {"budgetTokens": 1024}),
            },
            "updatedAt": now,
            "tokenSource": existing_settings.get("tokenSource", "migration"),
        }

        self._providers_file.write_text(json.dumps(data, indent=2) + "\n")

    def _update_models(
        self,
        model: tuple[str, str, int, str],
        provider_base_url: str | None = None,
    ) -> None:
        data: dict = {}
        if self._models_file.exists():
            try:
                data = json.loads(self._models_file.read_text())
            except json.JSONDecodeError:
                data = {}

        if "version" not in data:
            data["version"] = 1
        if "providers" not in data:
            data["providers"] = {}
        display_name, filename, port, container_name = model[0], model[1], model[2], model[3]
        ctx_size = _resolve_ctx_size(filename)

        base_url = provider_base_url or f"http://localhost:{port}"

        provider_config = data["providers"].get(self.PROVIDER_ID, {})
        existing_provider = provider_config.get("provider", {})
        existing_models = self._normalize_models(provider_config.get("models", []))

        model_entry = {
            "id": container_name,
            "name": display_name,
            "contextWindow": ctx_size,
            "maxInputTokens": ctx_size,
            "supportsImages": False,
            "capabilities": ["streaming"],
        }

        merged_models = [m for m in existing_models if m.get("id") != container_name] + [model_entry]

        data["providers"][self.PROVIDER_ID] = {
            "provider": {
                **existing_provider,
                "name": existing_provider.get("name", "OpenAI Compatible"),
                "baseUrl": f"{base_url}/v1",
                "defaultModelId": existing_provider.get("defaultModelId", container_name),
            },
            "models": merged_models,
        }

        for pid in list(data["providers"].keys()):
            if pid != self.PROVIDER_ID:
                provider_data = data["providers"][pid]
                p = provider_data.get("provider", {})
                if p.get("type") == "openai-compatible" or p.get("client") == "openai-compatible":
                    existing = self._normalize_models(provider_data.get("models", []))
                    merged = [m for m in existing if m.get("id") != container_name] + [model_entry]
                    data["providers"][pid] = {
                        **provider_data,
                        "models": merged,
                    }

        self._models_file.write_text(json.dumps(data, indent=2) + "\n")

    def _update_global_state(
        self,
        model: tuple[str, str, int, str]
    ) -> None:
        data: dict = {}
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
            except json.JSONDecodeError:
                data = {}

        display_name, filename, port, container_name = model[0], model[1], model[2], model[3]

        data["apiProvider"] = self.PROVIDER_ID
        data["actModeApiProvider"] = self.PROVIDER_ID
        data["planModeApiProvider"] = self.PROVIDER_ID
        data["api-provider"] = self.PROVIDER_ID
        data["act-mode-api-provider"] = self.PROVIDER_ID
        data["plan-mode-api-provider"] = self.PROVIDER_ID

        data["openAiModelId"] = container_name
        data["actModeOpenAiModelId"] = container_name
        data["planModeOpenAiModelId"] = container_name
        data["open-ai-model-id"] = container_name
        data["act-mode-open-ai-model-id"] = container_name
        data["plan-mode-open-ai-model-id"] = container_name

        data["openAiBaseUrl"] = f"http://localhost:{port}/v1"
        data["open-ai-base-url"] = f"http://localhost:{port}/v1"

        data["openAiApiKey"] = self._api_key

        provider_ids = [container_name, self.PROVIDER_ID]

        for pid in provider_ids:
            data[f"{pid}-model-id"] = container_name
            data[f"act-mode-{pid}-model-id"] = container_name
            data[f"plan-mode-{pid}-model-id"] = container_name

            cc_pid = self._to_camel_case(pid)
            data[f"{cc_pid}ModelId"] = container_name
            data[f"actMode{self._capitalize_first(cc_pid)}ModelId"] = container_name
            data[f"planMode{self._capitalize_first(cc_pid)}ModelId"] = container_name

        self._state_file.write_text(json.dumps(data, indent=2) + "\n")

    def _update_secrets(self) -> None:
        data: dict = {}
        if self._secrets_file.exists():
            try:
                data = json.loads(self._secrets_file.read_text())
            except json.JSONDecodeError:
                data = {}

        data["openAiApiKey"] = self._api_key

        self._secrets_file.write_text(json.dumps(data, indent=2) + "\n")

    @staticmethod
    def _normalize_models(models: list | dict) -> list:
        if isinstance(models, list):
            return models
        return list(models.values())

    def _to_camel_case(self, s: str) -> str:
        parts = s.split("-")
        processed_parts = []
        for p in parts:
            if p == "openai":
                processed_parts.append("openAi")
            else:
                processed_parts.append(p)

        res = processed_parts[0]
        for p in processed_parts[1:]:
            res += p.capitalize()
        return res

    def _capitalize_first(self, s: str) -> str:
        if not s:
            return s
        return s[0].upper() + s[1:]
