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
        self._state_file = cline_home / "globalState.json"

    def register_models(
        self,
        models: list[tuple[str, str, int]],
        provider_base_url: str | None = None,
    ) -> bool:
        if not models:
            self.logger.warn("No models to register with Cline")
            return False

        try:
            _, first_filename, first_port = models[0]
            base_url = provider_base_url or f"http://localhost:{first_port}"

            self._update_providers(first_filename, base_url)
            self._update_global_state(first_filename, base_url)
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
            return data.get("actModeOpenAiModelId") == model_name
        except Exception:
            return False

    def _update_providers(self, model_name: str, base_url: str) -> None:
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

        provider_id = "local llama"
        data["lastUsedProvider"] = provider_id
        data["providers"][provider_id] = {
            "settings": {
                "provider": "openai-compatible",
                "model": model_name,
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

    def _update_global_state(self, model_name: str, base_url: str) -> None:
        data: dict = {}
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
            except json.JSONDecodeError:
                data = {}

        data["actModeApiProvider"] = "local llama"
        data["planModeApiProvider"] = "local llama"
        data["actModeOpenAiModelId"] = model_name
        data["planModeOpenAiModelId"] = model_name
        data["openAiBaseUrl"] = f"{base_url}/v1"

        self._state_file.write_text(json.dumps(data, indent=2) + "\n")
