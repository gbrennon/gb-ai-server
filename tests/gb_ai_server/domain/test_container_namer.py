"""Tests for ContainerNamer domain logic."""

import pytest
from gb_ai_server.domain import ContainerNamer


class TestContainerForModel:
    def test_converts_colon_to_hyphen(self) -> None:
        assert ContainerNamer.container_for_model("qwen2.5-coder:7b") == "llama-qwen25-coder-7b"

    def test_removes_dots(self) -> None:
        assert ContainerNamer.container_for_model("deepseek.v2") == "llama-deepseekv2"

    def test_handles_simple_name(self) -> None:
        assert ContainerNamer.container_for_model("codellama") == "llama-codellama"

    def test_with_version_tag(self) -> None:
        assert ContainerNamer.container_for_model("mistral:latest") == "llama-mistral-latest"

    def test_lowercases(self) -> None:
        assert ContainerNamer.container_for_model("My-Model") == "llama-my-model"

    def test_collapses_multiple_hyphens(self) -> None:
        assert ContainerNamer.container_for_model("qwen---2.5") == "llama-qwen-25"

    def test_strips_special_chars(self) -> None:
        assert ContainerNamer.container_for_model("my@model!v2") == "llama-mymodelv2"

    def test_raises_on_empty_name(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            ContainerNamer.container_for_model("")

    def test_raises_on_blank_name(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            ContainerNamer.container_for_model("   ")
