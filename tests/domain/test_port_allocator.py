"""Tests for PortAllocator domain logic."""

import pytest
from gb_ai_server.domain import PortAllocator


class TestPortForModel:
    def test_first_model_gets_base_port(self) -> None:
        assert PortAllocator.port_for_model(0) == 8081

    def test_sequential_allocation(self) -> None:
        assert PortAllocator.port_for_model(1) == 8082
        assert PortAllocator.port_for_model(5) == 8086

    def test_raises_on_negative_index(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            PortAllocator.port_for_model(-1)


class TestPortsForModels:
    def test_single_model(self) -> None:
        assert PortAllocator.ports_for_models(1) == [8081]

    def test_multiple_models(self) -> None:
        assert PortAllocator.ports_for_models(3) == [8081, 8082, 8083]

    def test_raises_on_zero_count(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            PortAllocator.ports_for_models(0)

    def test_raises_on_negative_count(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            PortAllocator.ports_for_models(-1)
