"""Port allocation strategy."""


class PortAllocator:
    """Allocate ports for llama.cpp instances without conflicts."""

    BASE_PORT: int = 8081

    @staticmethod
    def port_for_model(model_index: int) -> int:
        if model_index < 0:
            raise ValueError("Model index cannot be negative")
        return PortAllocator.BASE_PORT + model_index

    @staticmethod
    def ports_for_models(count: int) -> list[int]:
        if count <= 0:
            raise ValueError("Model count must be positive")
        return [PortAllocator.port_for_model(i) for i in range(count)]
