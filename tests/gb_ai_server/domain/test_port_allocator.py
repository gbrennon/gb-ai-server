"""Tests for PortAllocator domain logic (single-model server)."""

import os
from unittest.mock import patch

import pytest
from gb_ai_server.domain import PortAllocator


class TestPort:
    def test_default_port(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert PortAllocator.port() == 8081

    def test_port_from_env_var(self) -> None:
        with patch.dict(os.environ, {"LLAMA_PORT": "9090"}):
            assert PortAllocator.port() == 9090

    def test_invalid_env_var_falls_back_to_default(self) -> None:
        with patch.dict(os.environ, {"LLAMA_PORT": "not-an-int"}):
            assert PortAllocator.port() == 8081
