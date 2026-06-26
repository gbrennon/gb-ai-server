"""Tests for presentation layer CLI entry point."""

from pathlib import Path
from unittest.mock import patch

from gb_ai_server.presentation.cli import build_parser, main


class TestBuildParser:
    def test_returns_parser_with_prog(self) -> None:
        parser = build_parser()
        assert parser.prog == "gb-ai-server"

    def test_defaults_are_correct(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.dry_run is False
        assert args.skip_download is False
        assert args.skip_health is False
        assert args.models_dir == Path("/tmp/llama_models")
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
        assert args.dry_run is True
        assert args.skip_download is True
        assert args.skip_health is True
        assert args.models_dir == Path("/custom/path")
        assert args.hf_token == "hf_abc123"
        assert args.debug is True


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
            with patch("gb_ai_server.presentation.cli.ClineModelRegistrar") as MockRegistrar:
                instance = MockRegistrar.return_value
                instance.register_models.return_value = register_return
                result = main(full_args)
                if register_return:
                    MockRegistrar.assert_called_once()
                    instance.register_models.assert_called_once()
                    call_args = instance.register_models.call_args
                    _, kwargs = call_args
                    models_arg = kwargs.get("models", args[0] if args else None)
                    assert models_arg is not None
                    assert len(models_arg) == 1
                    assert len(models_arg[0]) == 4
                    assert models_arg[0][3] == "llama-coder"
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
            with patch("gb_ai_server.presentation.cli.ClineModelRegistrar") as MockRegistrar:
                instance = MockRegistrar.return_value
                instance.register_models.return_value = True
                result = main([
                    "--register-models",
                    "--models-dir", str(models_dir),
                ])
                assert result == 0
                instance.register_models.assert_not_called()

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
            with patch("gb_ai_server.presentation.cli.ClineModelRegistrar") as MockRegistrar:
                instance = MockRegistrar.return_value
                instance.register_models.return_value = True

                result = main([
                    "--register-models",
                    "--models-dir", str(models_dir),
                    "--model", "model-b",
                ])

                assert result == 0
                call_args = instance.register_models.call_args
                _, kwargs = call_args
                models_arg = kwargs.get("models")
                assert len(models_arg) == 1
                assert models_arg[0][0] == "model-b"

    def test_register_models_with_bad_model_flag(self, tmp_path: Path) -> None:
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        conf_file = scripts_dir / "models.conf.sh"
        conf_file.write_text('MODELS=("model-a|a.gguf|https://example.com/a")\n')
        with patch("gb_ai_server.presentation.cli.Path.resolve", return_value=tmp_path):
            result = main(["--register-models", "--model", "nonexistent"])
            assert result == 1

