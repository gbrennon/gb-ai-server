"""HTTP client implementation using curl via shell command."""

from ..command import Command


class CurlHttpClient:
    """HTTP client using curl for health check requests."""

    def get(self, url: str, timeout_seconds: int = 5) -> bool:
        result = Command.run(
            "curl",
            "-sf",
            "--connect-timeout", str(timeout_seconds),
            "--max-time", str(timeout_seconds * 2),
            url,
            capture_output=True,
        )
        return result.success
