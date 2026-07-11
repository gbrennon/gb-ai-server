"""Mistral Vibe agent template — ~/.vibe/config.toml"""

from __future__ import annotations

import os
from pathlib import Path

PROVIDER_ID = "local llama.cpp"


def _vibe_dir() -> Path:
    env = os.environ.get("VIBE_HOME", "")
    return Path(env) if env else Path.home() / ".vibe"


def register(display_name: str, container_name: str, ctx_size: int, port: int = 8081) -> bool:
    vibe_home = _vibe_dir()
    vibe_home.mkdir(parents=True, exist_ok=True)
    config_path = vibe_home / "config.toml"

    existing_lines: list[str] = []
    if config_path.exists():
        existing_lines = config_path.read_text().splitlines()

    # Parse TOML to identify sections and filter out models belonging to PROVIDER_ID
    new_lines: list[str] = []
    i = 0
    in_provider_section = False
    in_model_section = False
    current_model_provider: str | None = None
    current_model_lines: list[str] = []
    model_entries_to_keep: list[list[str]] = []
    provider_section_lines: list[str] = []

    while i < len(existing_lines):
        line = existing_lines[i]

        # Flush pending model section when a new section starts
        if line.startswith("[[") and in_model_section:
            if current_model_provider != PROVIDER_ID:
                model_entries_to_keep.append(current_model_lines)
            current_model_lines = []
            in_model_section = False
            current_model_provider = None

        if line.startswith("[[") and in_provider_section:
            new_lines.extend(provider_section_lines)
            provider_section_lines = []
            in_provider_section = False

        if line.startswith("[[providers]]"):
            in_provider_section = True
            provider_section_lines = [line]
            i += 1
            continue

        if line.startswith("[[models]]"):
            in_model_section = True
            current_model_lines = [line]
            i += 1
            continue

        if in_provider_section:
            provider_section_lines.append(line)
            i += 1
            continue

        if in_model_section:
            current_model_lines.append(line)
            if line.strip().startswith("provider = "):
                current_model_provider = line.split('"')[1] if '"' in line else None
            i += 1
            continue

        new_lines.append(line)
        i += 1

    # Flush final sections
    if in_model_section and current_model_lines:
        if current_model_provider != PROVIDER_ID:
            model_entries_to_keep.append(current_model_lines)

    if in_provider_section:
        new_lines.extend(provider_section_lines)

    # Ensure provider section exists (update existing or add new)
    _add_or_update_provider(new_lines, port)

    # Re-add models NOT belonging to our provider
    for entry in model_entries_to_keep:
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        new_lines.extend(entry)

    # Add our single model
    if new_lines and new_lines[-1] != "":
        new_lines.append("")
    new_lines.extend([
        "[[models]]",
        f'name = "{container_name}"',
        f'provider = "{PROVIDER_ID}"',
        f'alias = "{display_name}"',
        'temperature = 0.2',
        'input_price = 0.0',
        'output_price = 0.0',
        'thinking = "off"',
        'supports_images = false',
        f'auto_compact_threshold = {ctx_size}',
    ])

    config_path.write_text("\n".join(new_lines) + "\n")

    # API key
    env_file = vibe_home / ".env"
    existing_env = env_file.read_text() if env_file.exists() else ""
    if "OPENAI_API_KEY=" not in existing_env:
        with open(env_file, "a") as f:
            f.write(f'OPENAI_API_KEY={os.environ.get("OPENAI_API_KEY", "dummy")}\n')

    return True


def _add_or_update_provider(lines: list[str], port: int) -> None:
    """Ensure the PROVIDER_ID provider exists, updating it if already present."""
    # Find existing provider block for PROVIDER_ID
    in_our_provider = False
    our_start: int | None = None

    for idx, line in enumerate(lines):
        if line.startswith("[[providers]]"):
            in_our_provider = False
            our_start = None
        if line.startswith("[[providers]]"):
            our_start = idx
            in_our_provider = True
            continue
        if line.startswith("[[") and in_our_provider:
            in_our_provider = False
            continue
        if in_our_provider and line.strip().startswith(f'name = "{PROVIDER_ID}"'):
            # Found our provider block — replace it
            if our_start is not None:
                block_end = our_start + 1
                while block_end < len(lines):
                    if lines[block_end].startswith("[["):
                        break
                    block_end += 1
                replacement = [
                    "[[providers]]",
                    f'name = "{PROVIDER_ID}"',
                    f'api_base = "http://localhost:{port}"',
                    'api_key_env_var = "OPENAI_API_KEY"',
                    'api_style = "openai"',
                    'backend = "generic"',
                ]
                lines[our_start:block_end] = replacement
                return

    # Provider not found — add it at the end
    if lines and lines[-1] != "":
        lines.append("")
    lines.extend([
        "[[providers]]",
        f'name = "{PROVIDER_ID}"',
        f'api_base = "http://localhost:{port}"',
        'api_key_env_var = "OPENAI_API_KEY"',
        'api_style = "openai"',
        'backend = "generic"',
    ])
