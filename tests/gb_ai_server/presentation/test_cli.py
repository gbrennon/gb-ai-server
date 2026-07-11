"""Tests for presentation layer CLI entry point."""

import os
from pathlib import Path
from unittest.mock import patch

from gb_ai_server.presentation.cli import build_parser, main, _normalize_models_dirs


class TestBuildParser:
    def test_returns_parser_with_prog(self) -> None:
        parser = build_parser()
        assert parser.prog == "gb-ai-server"

    def test_defaults_are_correct(self) -> None:
        with patch.dict(os.environ, {"MODELS_DIR": "/tmp/llama_models"}):
            parser = build_parser()
            args = parser.parse_args([])
            assert args.dry_run is False
            assert args.skip_download is False
            assert args.skip_health is False
            assert args.models_dir is None
            assert args.hf_token is None
            assert args.debug is False

    def test_parses_all_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "--dry-run",
                "--skip-download",
                "--skip-health",
                "--models-dir", "/custom/path",
                "--hf-token", "hf_abc123",
                "--debug",
            ]
        )
        _normalize_models_dirs(args)
        assert args.dry_run is True
        assert args.skip_download is True
        assert args.skip_health is True
        assert args.models_dir == Path("/custom/path")
        assert args.models_dirs == [Path("/custom/path")]
        assert args.hf_token == "hf_abc123"
        assert args.debug is True

    def test_parses_register_custom(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--register-custom", "unsloth/Qwen3-14B-GGUF"])
        assert args.register_custom == "unsloth/Qwen3-14B-GGUF"

    def test_parses_register_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--register"])
        assert args.register is True


class TestNormalizeModelsDirs:
    def test_single_dir_backward_compat(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--models-dir", "/single/path"])
        _normalize_models_dirs(args)
        assert args.models_dir == Path("/single/path")
        assert args.models_dirs == [Path("/single/path")]

    def test_colon_separated_multi_dir(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--models-dir", "/a:/b:/c"])
        _normalize_models_dirs(args)
        assert args.models_dir == Path("/a")
        assert args.models_dirs == [Path("/a"), Path("/b"), Path("/c")]

    def test_from_model_dirs_env_var(self) -> None:
        with patch.dict(os.environ, {"MODEL_DIRS": "/env/a:/env/b"}, clear=True):
            parser = build_parser()
            args = parser.parse_args([])
            _normalize_models_dirs(args)
            assert args.models_dir == Path("/env/a")
            assert args.models_dirs == [Path("/env/a"), Path("/env/b")]

    def test_fallback_to_models_dir_env_var(self) -> None:
        with patch.dict(os.environ, {"MODELS_DIR": "/legacy/path"}, clear=True):
            parser = build_parser()
            args = parser.parse_args([])
            _normalize_models_dirs(args)
            assert args.models_dir == Path("/legacy/path")
            assert args.models_dirs == [Path("/legacy/path")]

    def test_hardcoded_default_when_no_env(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            parser = build_parser()
            args = parser.parse_args([])
            _normalize_models_dirs(args)
            assert args.models_dir == Path("/tmp/llama_models")
            assert args.models_dirs == [Path("/tmp/llama_models")]


class TestMain:
    def test_delegates_to_composition_root(self) -> None:
        with patch("gb_ai_server.presentation.cli.BootstrapCompositionRoot") as MockRoot:
            instance = MockRoot.return_value
            instance.run.return_value = 0
            result = main(["--skip-download", "--skip-health"])
            assert result == 0
            MockRoot.assert_called_once()
            instance.run.assert_called_once()

    def test_returns_non_zero_when_root_fails(self) -> None:
        with patch("gb_ai_server.presentation.cli.BootstrapCompositionRoot") as MockRoot:
            instance = MockRoot.return_value
            instance.run.return_value = 1
            result = main(["--skip-download", "--skip-health"])
            assert result == 1

    def test_register_missing_config(self, tmp_path: Path) -> None:
        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            result = main(["--register"])
            assert result == 1

    def test_register_from_config(self, tmp_path: Path) -> None:
        (tmp_path / ".models.yaml").write_text("model:\n  id: test\n  file: t.gguf\n")
        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            with patch("gb_ai_server.application.services.register_custom_model_service.register_custom_model") as mock_reg:
                mock_reg.return_value = {"cline": True}
                result = main(["--register"])
                assert result == 0

    def test_register_custom(self) -> None:
        with patch("gb_ai_server.application.services.register_custom_model_service.register_custom_model") as mock_reg:
            mock_reg.return_value = {"cline": True, "opencode": True}
            result = main(["--register-custom", "test/repo"])
            assert result == 0
            mock_reg.assert_called_once_with("test/repo", 0)
