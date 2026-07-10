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
            assert args.models_dir is None  # raw; normalization happens in main()
            assert args.hf_token is None
            assert args.debug is False

    def test_parses_all_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "--dry-run",
                "--skip-download",
                "--skip-health",
                "--models-dir",
                "/custom/path",
                "--hf-token",
                "hf_abc123",
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
        with patch(
            "gb_ai_server.presentation.cli.BootstrapCompositionRoot"
        ) as MockRoot:
            instance = MockRoot.return_value
            instance.run.return_value = 0

            result = main(["--skip-download", "--skip-health"])

            assert result == 0
            MockRoot.assert_called_once()
            instance.run.assert_called_once()

    def test_returns_non_zero_when_root_fails(self) -> None:
        with patch(
            "gb_ai_server.presentation.cli.BootstrapCompositionRoot"
        ) as MockRoot:
            instance = MockRoot.return_value
            instance.run.return_value = 1

            result = main(["--skip-download", "--skip-health"])

            assert result == 1

    def _register_models_test(
        self, tmp_path: Path, args: list[str], register_return: bool
    ) -> int:
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        conf_file = scripts_dir / "models.conf.sh"
        conf_file.write_text('MODELS=("test-model:latest|test.gguf|https://example.com")\n')
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        (models_dir / "test.gguf").touch()

        full_args = [
            "--register-models",
            "--models-dir", str(models_dir),
            *args,
        ]
        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            with patch("gb_ai_server.presentation.cli.ModelPathResolver") as MockResolver:
                instance = MockResolver.return_value
                instance.resolve.return_value = models_dir / "test.gguf"
                with patch("gb_ai_server.presentation.cli.ClineModelRegistrar") as MockRegistrar:
                    cline_instance = MockRegistrar.return_value
                    cline_instance.register_model.return_value = register_return
                    result = main(full_args)
                    if register_return:
                        MockRegistrar.assert_called_once()
                        cline_instance.register_model.assert_called_once()
                        call_args = cline_instance.register_model.call_args
                        _, kwargs = call_args
                        model_arg = kwargs.get("model")
                        assert model_arg is not None
                        assert len(model_arg) == 4
                        assert model_arg[3] == "llama-coder"
                    return result

    def test_register_models_successful(self, tmp_path: Path) -> None:
        result = self._register_models_test(tmp_path, [], True)
        assert result == 0

    def test_register_models_failure(self, tmp_path: Path) -> None:
        result = self._register_models_test(tmp_path, [], False)
        assert result == 1

    def test_register_models_missing_config(self, tmp_path: Path) -> None:
        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            result = main(["--register-models"])
            assert result == 1

    def test_register_models_no_file_skips_registration(self, tmp_path: Path) -> None:
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        conf_file = scripts_dir / "models.conf.sh"
        conf_file.write_text('MODELS=("test-model:latest|test.gguf|https://example.com")\n')
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            with patch("gb_ai_server.presentation.cli.ModelPathResolver") as MockResolver:
                instance = MockResolver.return_value
                instance.resolve.return_value = None  # no file found
                with patch("gb_ai_server.presentation.cli.ClineModelRegistrar") as MockRegistrar:
                    cline_instance = MockRegistrar.return_value
                    cline_instance.register_model.return_value = True
                    result = main([
                        "--register-models",
                        "--models-dir", str(models_dir),
                    ])
                    assert result == 0
                    cline_instance.register_model.assert_not_called()

    def test_list_models(self, tmp_path: Path) -> None:
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        conf_file = scripts_dir / "models.conf.sh"
        conf_file.write_text(
            'MODELS=(\n'
            '  "model-a|a.gguf|https://example.com/a"\n'
            '  "model-b|b.gguf|https://example.com/b"\n'
            ')\n'
        )
        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            result = main(["--list-models"])
            assert result == 0

    def test_list_models_missing_config(self, tmp_path: Path) -> None:
        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            result = main(["--list-models"])
            assert result == 1

    def test_register_models_with_model_flag(self, tmp_path: Path) -> None:
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        conf_file = scripts_dir / "models.conf.sh"
        conf_file.write_text(
            'MODELS=(\n'
            '  "model-a|a.gguf|https://example.com/a"\n'
            '  "model-b|b.gguf|https://example.com/b"\n'
            ')\n'
        )
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        (models_dir / "b.gguf").touch()

        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            with patch("gb_ai_server.presentation.cli.ModelPathResolver") as MockResolver:
                resolve_mock = MockResolver.return_value
                resolve_mock.resolve.return_value = models_dir / "b.gguf"
                with patch("gb_ai_server.presentation.cli.ClineModelRegistrar") as MockRegistrar:
                    instance = MockRegistrar.return_value
                    instance.register_model.return_value = True

                    result = main([
                        "--register-models",
                        "--models-dir", str(models_dir),
                        "--model", "model-b",
                    ])

                    assert result == 0
                    call_args = instance.register_model.call_args
                    _, kwargs = call_args
                    model_arg = kwargs.get("model")
                    assert model_arg is not None
                    assert model_arg[0] == "model-b"

    def test_register_models_with_bad_model_flag(self, tmp_path: Path) -> None:
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        conf_file = scripts_dir / "models.conf.sh"
        conf_file.write_text('MODELS=("model-a|a.gguf|https://example.com/a")\n')
        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            result = main(["--register-models", "--model", "nonexistent"])
            assert result == 1

