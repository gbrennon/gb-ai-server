"""Service orchestration using compose tool."""

from pathlib import Path
from typing import Sequence

from ..core import Logger
from ..infrastructure import ComposeTool


class ServiceOrchestrator:
    """Orchestrate service lifecycle with compose tool."""

    def __init__(self, logger: Logger, compose_tool: ComposeTool) -> None:
        """
        Initialize orchestrator.

        Args:
            logger: Logger instance.
            compose_tool: Compose tool to use.
        """
        self.logger = logger
        self.compose_tool = compose_tool

    def start_services(
        self,
        compose_file: Path,
        *services: str,
    ) -> bool:
        """
        Start services.

        Args:
            compose_file: Path to compose file.
            services: Service names to start (empty = all).

        Returns:
            True if successful.
        """
        self.logger.section("Starting Services")

        if not services:
            services = ()

        result = self.compose_tool.up(
            compose_file,
            *services,
            detach=True,
        )

        if result.success:
            self.logger.ok("Services started")
            return True
        else:
            self.logger.error("Failed to start services")
            if result.stderr:
                self.logger.debug(result.stderr)
            return False

    def stop_services(self, compose_file: Path) -> bool:
        """
        Stop all services.

        Args:
            compose_file: Path to compose file.

        Returns:
            True if successful.
        """
        self.logger.section("Stopping Services")

        result = self.compose_tool.down(compose_file)

        if result.success:
            self.logger.ok("Services stopped")
            return True
        else:
            self.logger.warn("Failed to stop services gracefully")
            # Non-fatal error
            return False

    def restart_services(
        self,
        compose_file: Path,
        *services: str,
    ) -> bool:
        """
        Restart services.

        Args:
            compose_file: Path to compose file.
            services: Service names to restart.

        Returns:
            True if successful.
        """
        self.logger.section("Restarting Services")

        if not services:
            services = ()

        result = self.compose_tool.restart(compose_file, *services)

        if result.success:
            self.logger.ok("Services restarted")
            return True
        else:
            self.logger.error("Failed to restart services")
            if result.stderr:
                self.logger.debug(result.stderr)
            return False

    def list_services(self, compose_file: Path) -> bool:
        """
        List running services.

        Args:
            compose_file: Path to compose file.

        Returns:
            True if successful.
        """
        self.logger.section("Service Status")

        result = self.compose_tool.ps(compose_file)

        if result.success:
            print(result.stdout)
            return True
        else:
            self.logger.warn("No services running")
            return False

    def show_logs(
        self,
        compose_file: Path,
        service: str | None = None,
        follow: bool = False,
    ) -> bool:
        """
        Show service logs.

        Args:
            compose_file: Path to compose file.
            service: Specific service (None = all).
            follow: Follow logs in real-time.

        Returns:
            True if successful.
        """
        result = self.compose_tool.logs(
            compose_file,
            service=service,
            follow=follow,
        )

        if result.success:
            if result.stdout:
                print(result.stdout)
            return True
        else:
            self.logger.error("Failed to retrieve logs")
            return False
