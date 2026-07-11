"""Environment path utilities."""

from pathlib import Path


class EnvironmentPaths:
    """Computed paths derived from repo root."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    @property
    def scripts_lib_dir(self) -> Path:
        return self._repo_root / "scripts" / "lib"

    @property
    def models_config_path(self) -> Path:
        return self._repo_root / ".models.yaml"

    @property
    def compose_file(self) -> Path:
        return self._repo_root / "docker-compose.yml"

    @property
    def env_file(self) -> Path:
        return self._repo_root / ".env"
