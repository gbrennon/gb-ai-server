"""Model configuration file parser (bash-format models.conf.sh)."""

from pathlib import Path

from gb_ai_server.domain import ModelEntry


def _strip_array_declaration(line: str) -> str:
    if line.startswith("MODELS=("):
        return line[8:]
    return line


def _is_array_end(line: str) -> bool:
    return line.endswith(")")


def _strip_array_end(line: str) -> str:
    return line[:-1] if _is_array_end(line) else line


def _parse_entry(line: str) -> ModelEntry | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    line = line.strip('"\'')
    return ModelEntry.from_string(line) if line else None


def load_models(models_conf_path: Path) -> list[ModelEntry]:
    """Parse a bash-format models.conf.sh file into ModelEntry instances."""
    if not models_conf_path.exists():
        raise ValueError(f"Models config not found: {models_conf_path}")

    models: list[ModelEntry] = []
    with open(models_conf_path) as f:
        in_array = False
        for line in f:
            line = line.strip()

            if line.startswith("MODELS=("):
                in_array = True
                line = _strip_array_declaration(line)

            if not in_array:
                continue

            if _is_array_end(line):
                line = _strip_array_end(line)
                in_array = False

            entry = _parse_entry(line)
            if entry:
                models.append(entry)

    return models
