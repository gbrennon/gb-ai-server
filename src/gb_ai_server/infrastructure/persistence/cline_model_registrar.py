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
      - ~/.cline/data/settings/models.json     — provider models catalog
      - ~/.cline/data/globalState.json          — provider model mappings
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
            self._update_global_state(models)

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
            if model_id == model_name:
                return True
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
                    "provider": "openai-compatible",
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

            # Register the built-in compatible provider IDs ONLY if they do not exist
            # or if they are currently pointing to localhost (safe to overwrite)
            cli_provider_id = "openai-compatible" if idx == 0 else "openai-native"
            should_write_cli = True
            if cli_provider_id in data["providers"]:
                settings = data["providers"][cli_provider_id].get("settings", {})
                existing_url = settings.get("baseUrl", "")
                if existing_url and "localhost" not in existing_url and "127.0.0.1" not in existing_url:
                    should_write_cli = False

            if should_write_cli:
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

            # Also register under the built-in compatible provider IDs so the select box has them
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

    def _update_global_state(self, models: list[tuple[str, str, int, str]]) -> None:
        data: dict = {}
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
            except json.JSONDecodeError:
                data = {}

        # If the active provider is "llama-coder" (which is invalid in TUI/CLI),
        # automatically change it to "openai-compatible" so the TUI/CLI can run.
        provider_id = "openai-compatible"
        current_provider = data.get("apiProvider", "")
        if current_provider == "llama-coder":
            data["apiProvider"] = provider_id
            data["actModeApiProvider"] = provider_id
            data["planModeApiProvider"] = provider_id
            data["api-provider"] = provider_id
            data["act-mode-api-provider"] = provider_id
            data["plan-mode-api-provider"] = provider_id

            first_display_name, first_filename, first_port, first_container = models[0]
            data["openAiModelId"] = first_filename
            data["actModeOpenAiModelId"] = first_filename
            data["planModeOpenAiModelId"] = first_filename
            data["open-ai-model-id"] = first_filename
            data["act-mode-open-ai-model-id"] = first_filename
            data["plan-mode-open-ai-model-id"] = first_filename
            data["openAiBaseUrl"] = f"http://localhost:{first_port}/v1"
            data["open-ai-base-url"] = f"http://localhost:{first_port}/v1"

        for idx, (display_name, filename, port, container_name) in enumerate(models):
            provider_ids = [container_name]
            if idx == 0:
                provider_ids.append("openai-compatible")
            else:
                provider_ids.append("openai-native")

            for pid in provider_ids:
                # Kebab case keys
                data[f"{pid}-model-id"] = filename
                data[f"act-mode-{pid}-model-id"] = filename
                data[f"plan-mode-{pid}-model-id"] = filename

                # Camel case keys
                cc_pid = self._to_camel_case(pid)
                data[f"{cc_pid}ModelId"] = filename
                data[f"actMode{self._capitalize_first(cc_pid)}ModelId"] = filename
                data[f"planMode{self._capitalize_first(cc_pid)}ModelId"] = filename

        self._state_file.write_text(json.dumps(data, indent=2) + "\n")

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
