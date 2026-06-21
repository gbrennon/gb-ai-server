"""Port allocation strategy."""


class PortAllocator:
    """Allocate ports for llama.cpp instances without conflicts."""

    BASE_PORT: int = 8081

    @classmethod
    def port_for_model(cls, model_index: int) -> int:
        """
        Derive port from model index.

        Ensures sequential allocation: 8081, 8082, 8083, ...

        Args:
            model_index: Zero-based model index.

        Returns:
            Port number.

        Raises:
            ValueError: If index is negative.
        """
        if model_index < 0:
            raise ValueError("Model index cannot be negative")
        return cls.BASE_PORT + model_index

    @classmethod
    def ports_for_models(cls, count: int) -> list[int]:
        """
        Get ports for N models.

        Args:
            count: Number of models.

        Returns:
            List of port numbers.

        Raises:
            ValueError: If count is non-positive.
        """
        if count <= 0:
            raise ValueError("Model count must be positive")
        return [cls.port_for_model(i) for i in range(count)]
