"""Health check strategy and URL generation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthCheckStrategy:
    """Health check configuration for a service."""

    host: str = "localhost"
    path: str = "/health"

    def url(self, port: int) -> str:
        """
        Generate health check URL for given port.

        Args:
            port: Service port.

        Returns:
            Full health check URL (e.g., "http://localhost:8081/health").
        """
        return f"http://{self.host}:{port}{self.path}"
