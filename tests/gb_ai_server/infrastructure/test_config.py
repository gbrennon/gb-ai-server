"""Integration tests for Environment config edge cases."""

from pathlib import Path

from gb_ai_server.infrastructure.config import Environment, EnvironmentPaths


class TestEnvironment:
    def test_from_env_uses_defaults(self) -> None:
        env = Environment.from_env()
        assert isinstance(env.repo_root, Path)
        assert env.repo_root.is_absolute()

    def test_from_env_uses_actual_env_vars(self) -> None:
        import os
        os.environ["REPO_ROOT"] = "/tmp/test-repo"
        os.environ["DEBUG"] = "true"
        try:
            env = Environment.from_env()
            assert str(env.repo_root) == "/tmp/test-repo"
            assert env.debug is True
        finally:
            del os.environ["REPO_ROOT"]
            del os.environ["DEBUG"]

    def test_default_debug_is_false(self) -> None:
        env = Environment.from_env()
        assert env.debug is False


class TestEnvironmentPaths:
    def test_compose_file(self) -> None:
        paths = EnvironmentPaths(Path("/tmp/test-repo"))
        assert str(paths.compose_file) == "/tmp/test-repo/docker-compose.yml"

    def test_models_config_path(self) -> None:
        paths = EnvironmentPaths(Path("/tmp/test-repo"))
        assert str(paths.models_config_path) == "/tmp/test-repo/scripts/models.conf.sh"

    def test_scripts_lib_dir(self) -> None:
        paths = EnvironmentPaths(Path("/tmp/test-repo"))
        assert str(paths.scripts_lib_dir) == "/tmp/test-repo/scripts/lib"

    def test_env_file(self) -> None:
        paths = EnvironmentPaths(Path("/tmp/test-repo"))
        assert str(paths.env_file) == "/tmp/test-repo/.env"

    def test_paths_property(self) -> None:
        env = Environment.from_env(repo_root=Path("/tmp/test-repo"))
        assert str(env.paths.scripts_lib_dir) == "/tmp/test-repo/scripts/lib"

    def test_env_file_paths_property(self) -> None:
        env = Environment.from_env(repo_root=Path("/tmp/test-repo"))
        assert str(env.paths.env_file) == "/tmp/test-repo/.env"

    def test_load_env_file_skips_comments(self, tmp_path: Path) -> None:
        import os
        env_file = tmp_path / ".env"
        env_file.write_text("# this is a comment\nKEY=value\n")
        Environment.load_env_file(env_file)
        assert os.environ.get("KEY") == "value"
        del os.environ["KEY"]

    def test_load_env_file_skips_empty_lines(self, tmp_path: Path) -> None:
        import os
        env_file = tmp_path / ".env"
        env_file.write_text("\n\nKEY2=value2\n")
        Environment.load_env_file(env_file)
        assert os.environ.get("KEY2") == "value2"
        del os.environ["KEY2"]

    def test_load_env_file_skips_lines_without_equals(self, tmp_path: Path) -> None:
        import os
        env_file = tmp_path / ".env"
        env_file.write_text("JUST_TEXT\nKEY3=value3\n")
        Environment.load_env_file(env_file)
        assert "JUST_TEXT" not in os.environ
        assert os.environ.get("KEY3") == "value3"
        del os.environ["KEY3"]

    def test_load_env_file_nonexistent_does_nothing(self) -> None:
        env = Environment.from_env()
        env.load_env_file(Path("/nonexistent/.env"))  # should not raise
        assert True
