"""Cline agent template — ~/.cline/data/settings/"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROVIDER_ID = "local llama.cpp"


def _cline_data_dir() -> Path:
    env = os.environ.get("CLINE_DATA_DIR", "")
    return Path(env) if env else Path.home() / ".cline" / "data"


def _read_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def _normalize_models(models: list | dict) -> list:
    return models if isinstance(models, list) else list(models.values())


def _probe_server_ctx(port: int) -> int | None:
    """Ask the running llama.cpp server what n_ctx it actually started with."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/props", timeout=3) as resp:
            data = json.loads(resp.read())
            gen = data.get("default_generation_settings", {})
            n_ctx = gen.get("n_ctx") or gen.get("params", {}).get("n_ctx")
            return int(n_ctx) if n_ctx else None
    except Exception:
        return None


def register(display_name: str, container_name: str, ctx_size: int, port: int = 8081, n_gpu_layers: int = 999) -> bool:
    cline_dir = _cline_data_dir()
    settings_dir = cline_dir / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)

    providers_file = settings_dir / "providers.json"
    models_file = settings_dir / "models.json"
    secrets_file = cline_dir / "secrets.json"

    # Use the actual server n_ctx when available — it's the ground truth.
    # Falls back to the configured ctx_size if the server isn't reachable yet.
    actual_ctx = _probe_server_ctx(port) or ctx_size

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    api_key = os.environ.get("OPENAI_API_KEY", "dummy")
    base_url = f"http://localhost:{port}"

    # --- providers.json ---
    providers = _read_json(providers_file)
    providers.setdefault("providers", {})
    existing = providers["providers"].get(PROVIDER_ID, {})
    existing_settings = existing.get("settings", {})
    existing_default = existing_settings.get("model", "")

    providers["lastUsedProvider"] = PROVIDER_ID
    providers["providers"][PROVIDER_ID] = {
        "settings": {
            "provider": PROVIDER_ID,
            "apiKey": existing_settings.get("apiKey", api_key),
            "model": existing_default,
            "baseUrl": f"{base_url}/v1",
            "timeout": existing_settings.get("timeout", 30000),
            "reasoning": existing_settings.get("reasoning", {"budgetTokens": 1024}),
        },
        "updatedAt": now,
        "tokenSource": existing_settings.get("tokenSource", "migration"),
    }
    providers_file.write_text(json.dumps(providers, indent=2) + "\n")

    # --- models.json ---
    models = _read_json(models_file)
    models.setdefault("version", 1)
    models.setdefault("providers", {})

    pc = models["providers"].get(PROVIDER_ID, {})
    existing_prov_data = pc.get("provider", {})
    existing_models = _normalize_models(pc.get("models", []))

    model_entry = {
        "id": container_name,
        "name": display_name,
        "contextWindow": actual_ctx,
        "maxInputTokens": actual_ctx,
        "supportsImages": False,
        "capabilities": ["streaming"],
    }

    merged = [model_entry]
    existing_default_id = existing_prov_data.get("defaultModelId")

    models["providers"][PROVIDER_ID] = {
        "provider": {
            **existing_prov_data,
            "name": existing_prov_data.get("name", "local llama.cpp"),
            "baseUrl": f"{base_url}/v1",
            "defaultModelId": existing_default_id or container_name,
        },
        "models": merged,
    }

    models_file.write_text(json.dumps(models, indent=2) + "\n")

    # --- secrets.json ---
    secrets = _read_json(secrets_file)
    secrets["openAiApiKey"] = api_key
    secrets_file.write_text(json.dumps(secrets, indent=2) + "\n")

    # --- globalState.json ---
    state_file = cline_dir / "globalState.json"
    state = _read_json(state_file)

    state["apiProvider"] = PROVIDER_ID
    state["actModeApiProvider"] = PROVIDER_ID
    state["planModeApiProvider"] = PROVIDER_ID
    state["api-provider"] = PROVIDER_ID
    state["act-mode-api-provider"] = PROVIDER_ID
    state["plan-mode-api-provider"] = PROVIDER_ID

    state["openAiModelId"] = container_name
    state["actModeOpenAiModelId"] = container_name
    state["planModeOpenAiModelId"] = container_name
    state["open-ai-model-id"] = container_name
    state["act-mode-open-ai-model-id"] = container_name
    state["plan-mode-open-ai-model-id"] = container_name

    state["openAiBaseUrl"] = f"http://localhost:{port}/v1"
    state["open-ai-base-url"] = f"http://localhost:{port}/v1"
    state["openAiApiKey"] = api_key

    # CamelCase and kebab-case provider-specific keys
    provider_ids = [container_name, PROVIDER_ID]
    for pid in provider_ids:
        state[f"{pid}-model-id"] = container_name
        state[f"act-mode-{pid}-model-id"] = container_name
        state[f"plan-mode-{pid}-model-id"] = container_name

        cc_pid = _to_camel_case(pid)
        state[f"{cc_pid}ModelId"] = container_name
        state[f"actMode{cc_pid[0].upper() + cc_pid[1:]}ModelId"] = container_name
        state[f"planMode{cc_pid[0].upper() + cc_pid[1:]}ModelId"] = container_name

    state_file.write_text(json.dumps(state, indent=2) + "\n")

    return True


def _to_camel_case(s: str) -> str:
    """Convert kebab-case/space-separated to camelCase (e.g. 'local llama.cpp' -> 'localLlamaCpp')."""
    # Normalize: replace spaces with dashes, strip dots from sub-parts
    cleaned = s.replace(" ", "-").replace(".", "-")
    parts = cleaned.split("-")
    parts = [p for p in parts if p]  # filter empty strings
    if not parts:
        return ""
    res = parts[0]
    for p in parts[1:]:
        res += p.capitalize()
    return res
