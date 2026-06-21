"""Environment and configuration management."""

from pathlib import Path
from dataclasses import dataclass
import os


@dataclass
class Environment:
    """Environment configuration and variable management."""

    repo_root: Path
    dry_run: bool = False
    debug: bool = False

    @classmethod
    def from_env(
        cls,
        repo_root: Path | None = None,
    ) -> "Environment":
        """
        Load environment from OS variables and .env file.

        Args:
            repo_root: Repository root path. If None, inferred from REPO_ROOT env.

        Returns:
            Environment instance.
        """
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

    @classmethod
    def load_env_file(cls, env_file: Path) -> None:
        """
        Load variables from .env file into os.environ.

        Args:
            env_file: Path to .env file.
        """
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
    def scripts_lib_dir(self) -> Path:
        """Get scripts/lib directory path."""
        return self.repo_root / "scripts" / "lib"

    @property
    def models_config_path(self) -> Path:
        """Get models.conf.sh path."""
        return self.repo_root / "scripts" / "models.conf.sh"

    @property
    def compose_file(self) -> Path:
        """Get docker-compose.yml path."""
        return self.repo_root / "docker-compose.yml"

    @property
    def env_file(self) -> Path:
        """Get .env file path."""
        return self.repo_root / ".env"
