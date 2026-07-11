"""Tests for ContainerNamer domain logic (single-model server)."""

import os
from unittest.mock import patch

import pytest
from gb_ai_server.domain import ContainerNamer


class TestName:
    def test_default_name(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert ContainerNamer.name() == "llama-coder"

    def test_name_from_env_var(self) -> None:
        with patch.dict(os.environ, {"LLAMA_CONTAINER_NAME": "my-custom-container"}):
            assert ContainerNamer.name() == "my-custom-container"
