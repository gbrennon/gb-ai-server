"""Cline model registrar - registers local models with Cline."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ...application.ports.outbound.logger import Logger


class ClineModelRegistrar:
    """Register local models with Cline by updating ~/.cline/ configuration.

    Writes to:
      - ~/.cline/data/settings/providers.json  — provider entries with base URLs
      - ~/.cline/data/globalState.json          — active provider and model
    """

    def __init__(
        self,
        logger: Logger,
        cline_data_dir: str | Path | None = None,
    ) -> None:
        self.logger = logger
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

    def register_models(
        self,
        models: list[tuple[str, str, int, str]],
        provider_base_url: str | None = None,
    ) -> bool:
        if not models:
            self.logger.warn("No models to register with Cline")
            return False

        try:
            self._update_providers(models, provider_base_url)
            self._update_models(models, provider_base_url)

            first_display_name, first_filename, first_port, first_container = models[0]
            first_base_url = provider_base_url or f"http://localhost:{first_port}"
            # Use non-prefixed model ID for global state (like ollama provider)
            self._update_global_state(first_display_name, first_filename, first_base_url, first_container)

            self.logger.ok(
                f"Registered {len(models)} model(s) with Cline"
            )
            return True
        except Exception as e:
            self.logger.warn(f"Failed to register models with Cline: {e}")
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
            # Check if provider is a llama container (starts with "llama-")
            # Model ID in state is non-prefixed (like ollama provider)
            # Accept both prefixed and non-prefixed model names for backward compatibility
            if model_id == model_name:
                return True
            # Check if model_name is provider-prefixed and matches
            if provider and provider.startswith("llama-") and model_name.startswith(f"{provider}/"):
                return model_id == model_name.removeprefix(f"{provider}/")
            return provider is not None and provider.startswith("llama-") and model_id == model_name
        except Exception:
            return False

    def _update_providers(
        self,
        models: list[tuple[str, str, int, str]],
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

        now = datetime.now(timezone.utc).isoformat()

        # Remove legacy keys
        if "providers" in data:
            for key in list(data["providers"].keys()):
                if key.startswith("local llama") or key.startswith("local-llama"):
                    data["providers"].pop(key, None)

        for idx, (display_name, filename, port, container_name) in enumerate(models):
            # Use container name for provider ID (e.g., "llama-coder", "llama-qwen3")
            provider_id = container_name if idx == 0 else f"{container_name}"
            base_url = provider_base_url or f"http://localhost:{port}"

            if idx == 0:
                data["lastUsedProvider"] = provider_id

            # Register the custom provider ID with container name
            data["providers"][provider_id] = {
                "settings": {
                    "provider": provider_id,
                    "model": filename,
                    "baseUrl": f"{base_url}/v1",
                    "apiKey": "dummy",
                    "reasoning": {
                        "enabled": False,
                    },
                },
                "updatedAt": now,
                "tokenSource": "migration",
            }

            # Register the corresponding built-in CLI compatibility provider ID
            cli_provider_id = "openai-compatible" if idx == 0 else "openai-native"
            data["providers"][cli_provider_id] = {
                "settings": {
                    "provider": cli_provider_id,
                    "model": filename,
                    "baseUrl": f"{base_url}/v1",
                    "apiKey": "dummy",
                    "reasoning": {
                        "enabled": False,
                    },
                },
                "updatedAt": now,
                "tokenSource": "migration",
            }

        self._providers_file.write_text(json.dumps(data, indent=2) + "\n")

    def _update_global_state(self, display_name: str, model_name: str, base_url: str, container_name: str) -> None:
        data: dict = {}
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
            except json.JSONDecodeError:
                data = {}

        provider_id = container_name

        # Set camelCase keys
        data["apiProvider"] = provider_id
        data["actModeApiProvider"] = provider_id
        data["planModeApiProvider"] = provider_id
        data["openAiModelId"] = model_name
        data["actModeOpenAiModelId"] = model_name
        data["planModeOpenAiModelId"] = model_name
        data["openAiBaseUrl"] = f"{base_url}/v1"

        # Set kebab-case keys for CLI compatibility
        data["api-provider"] = provider_id
        data["act-mode-api-provider"] = provider_id
        data["plan-mode-api-provider"] = provider_id
        data["open-ai-model-id"] = model_name
        data["act-mode-open-ai-model-id"] = model_name
        data["plan-mode-open-ai-model-id"] = model_name
        data["open-ai-base-url"] = f"{base_url}/v1"

        self._state_file.write_text(json.dumps(data, indent=2) + "\n")

    def _update_models(
        self,
        models: list[tuple[str, str, int, str]],
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

        # Remove legacy root-level provider keys if they exist
        for key in list(data.keys()):
            if key.startswith("local llama") or key.startswith("local-llama"):
                data.pop(key, None)

        if "providers" in data:
            for key in list(data["providers"].keys()):
                if key.startswith("local llama") or key.startswith("local-llama"):
                    data["providers"].pop(key, None)

        # Build all models dict with non-prefixed IDs (e.g., "model.gguf") like ollama provider
        all_models: dict[str, dict] = {}
        for display_name, filename, port, container_name in models:
            all_models[filename] = {
                "id": filename,
                "name": filename,
                "contextWindow": 8192,
                "maxInputTokens": 8192,
                "capabilities": ["streaming", "tools"],
                "supportsVision": False,
                "supportsAttachments": False,
                "supportsReasoning": False,
            }

        # Register each container as a provider with ALL models
        for idx, (display_name, filename, port, container_name) in enumerate(models):
            # Use container name for provider ID (e.g., "llama-coder", "llama-qwen3")
            provider_id = container_name
            base_url = provider_base_url or f"http://localhost:{port}"
            default_model_id = filename  # Non-prefixed like ollama provider

            data["providers"][provider_id] = {
                "provider": {
                    "name": provider_id,
                    "baseUrl": f"{base_url}/v1",
                    "defaultModelId": default_model_id,
                    "protocol": "openai-chat",
                    "client": "openai-compatible",
                    # llama.cpp has /models endpoint for model discovery
                    "modelsSourceUrl": f"{base_url}/models",
                },
                "models": all_models.copy()
            }

            cli_provider_id = "openai-compatible" if idx == 0 else "openai-native"
            data["providers"][cli_provider_id] = {
                "provider": {
                    "name": "OpenAI Compatible" if idx == 0 else "OpenAI Native",
                    "baseUrl": f"{base_url}/v1",
                    "defaultModelId": default_model_id,
                    "protocol": "openai-chat",
                    "client": "openai-compatible",
                    "modelsSourceUrl": f"{base_url}/models",
                },
                "models": all_models.copy()
            }

        self._models_file.write_text(json.dumps(data, indent=2) + "\n")
