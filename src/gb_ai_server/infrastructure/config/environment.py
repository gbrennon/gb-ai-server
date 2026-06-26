"""Environment and configuration management."""

from pathlib import Path
from dataclasses import dataclass
import os

from .paths import EnvironmentPaths


@dataclass
class Environment:
    """Environment configuration from OS variables and .env files."""

    repo_root: Path
    dry_run: bool = False
    debug: bool = False

    @classmethod
    def from_env(
        cls,
        repo_root: Path | None = None,
    ) -> "Environment":
        if repo_root is None:
            repo_root_str = os.getenv("REPO_ROOT", ".")
            repo_root = Path(repo_root_str).resolve()

        dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        debug = os.getenv("DEBUG", "false").lower() == "true"

        return cls(
            repo_root=repo_root,
            dry_run=dry_run,
            debug=debug,
        )

    @staticmethod
    def load_env_file(env_file: Path) -> None:
        if not env_file.exists():
            return

        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

    @property
    def paths(self) -> EnvironmentPaths:
        return EnvironmentPaths(self.repo_root)
