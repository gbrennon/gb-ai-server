"""Integration tests for CurlHttpClient (fixture HTTP server, no external network)."""

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import pytest

from gb_ai_server.infrastructure.http.curl_client import CurlHttpClient


class _TestHealthHandler(BaseHTTPRequestHandler):
    """Returns 200 on /health, 404 elsewhere."""

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        pass


@pytest.fixture(scope="module")
def health_server() -> int:
    server = HTTPServer(("127.0.0.1", 0), _TestHealthHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield port
    server.shutdown()


class TestCurlHttpClient:
    def test_returns_true_for_healthy_endpoint(self, health_server: int) -> None:
        client = CurlHttpClient()
        result = client.get(f"http://127.0.0.1:{health_server}/health")
        assert result is True

    def test_returns_false_for_404(self, health_server: int) -> None:
        client = CurlHttpClient()
        result = client.get(f"http://127.0.0.1:{health_server}/nonexistent")
        assert result is False

    def test_returns_false_for_refused_connection(self) -> None:
        client = CurlHttpClient()
        result = client.get("http://127.0.0.1:1/health", timeout_seconds=1)
        assert result is False
