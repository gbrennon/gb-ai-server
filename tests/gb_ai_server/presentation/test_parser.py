"""Tests for YAML model parser."""

from pathlib import Path

import pytest

from gb_ai_server.presentation.parser import load_models


class TestLoadModels:
    def test_parses_yaml_model(self, tmp_path: Path) -> None:
        conf = tmp_path / ".models.yaml"
        conf.write_text(
            "model:\n"
            "  id: unsloth/Qwen3-14B-GGUF\n"
            "  file: Qwen3-14B-Q4_K_M.gguf\n"
            "  gpu_layers: 999\n"
            "  ctx_size: 40960\n"  # accepted in YAML but not stored — HF lib is source of truth
        )
        models = load_models(conf)
        assert len(models) == 1
        assert models[0].display_name == "Qwen3-14B-GGUF"
        assert models[0].filename == "Qwen3-14B-Q4_K_M.gguf"
        assert models[0].n_gpu_layers == 999
        assert not hasattr(models[0], "ctx_size")

    def test_parses_minimal_yaml(self, tmp_path: Path) -> None:
        conf = tmp_path / ".models.yaml"
        conf.write_text("model:\n  id: unsloth/Qwen3-14B-GGUF\n  file: model.gguf\n")
        models = load_models(conf)
        assert len(models) == 1
        assert models[0].display_name == "Qwen3-14B-GGUF"
        assert models[0].filename == "model.gguf"

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(ValueError, match="not found"):
            load_models(missing)

    def test_raises_on_missing_model_key(self, tmp_path: Path) -> None:
        conf = tmp_path / ".models.yaml"
        conf.write_text("something: else\n")
        with pytest.raises(ValueError, match="missing 'model'"):
            load_models(conf)

    def test_raises_on_missing_id(self, tmp_path: Path) -> None:
        conf = tmp_path / ".models.yaml"
        conf.write_text("model:\n  file: model.gguf\n")
        with pytest.raises(ValueError, match="missing 'id'"):
            load_models(conf)

    def test_defaults_gpu_layers(self, tmp_path: Path) -> None:
        conf = tmp_path / ".models.yaml"
        conf.write_text("model:\n  id: unsloth/Qwen3-14B-GGUF\n  file: model.gguf\n")
        models = load_models(conf)
        assert models[0].n_gpu_layers == 999

    def test_no_ctx_size_on_model_entry(self, tmp_path: Path) -> None:
        # ctx_size is not stored on ModelEntry — the HF lib computes it at runtime.
        conf = tmp_path / ".models.yaml"
        conf.write_text("model:\n  id: unsloth/Qwen3-14B-GGUF\n  file: model.gguf\n")
        models = load_models(conf)
        assert not hasattr(models[0], "ctx_size")
