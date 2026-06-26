"""Service implementation for health verification."""

from ..ports.outbound.logger import Logger
from ..ports.outbound.http_client import HttpClient
from ...domain import HealthCheckStrategy, WaitStrategy
from ..dtos.requests.verify_health_request import VerifyHealthRequest
from ..dtos.responses.verify_health_response import VerifyHealthResponse
from ..utils import print_section


class HealthVerifierService:
    """Verify service health via HTTP endpoints."""

    def __init__(self, logger: Logger, http_client: HttpClient) -> None:
        self.logger = logger
        self._http_client = http_client

    def execute(self, request: VerifyHealthRequest) -> VerifyHealthResponse:
        print_section("Health Verification")

        strategy = HealthCheckStrategy()
        all_healthy = True

        for port in request.ports:
            endpoint = strategy.url(port)
            if not self._verify_endpoint(
                endpoint,
                request.timeout_seconds,
                request.interval_seconds,
            ):
                all_healthy = False

        return VerifyHealthResponse(all_healthy)

    def _verify_endpoint(
        self,
        endpoint: str,
        timeout_seconds: int,
        interval_seconds: int,
    ) -> bool:
        self.logger.info(f"Checking {endpoint}...")

        wait_strategy = WaitStrategy(
            max_retries=timeout_seconds // interval_seconds,
            initial_interval_seconds=float(interval_seconds),
        )

        def is_healthy() -> bool:
            return self._http_client.get(endpoint)

        def on_retry(attempt: int, interval: float) -> None:
            self.logger.debug(
                f"Retry {attempt}: waiting {interval}s before next check"
            )

        if wait_strategy.wait_for_condition(is_healthy, on_retry=on_retry):
            self.logger.ok(f"Service on {endpoint} is healthy")
            return True
        else:
            self.logger.warn(
                f"Service on {endpoint} did not become healthy in time"
            )
            return False
