"""System prerequisite verification service."""

from pathlib import Path

from ..core import Logger, Command
from ..infrastructure import (
    ContainerRuntime,
    ComposeTool,
    RuntimeDetector,
    ComposeToolDetector,
)


class PrerequisiteVerifier:
    """Verify system prerequisites for bootstrap."""

    def __init__(self, logger: Logger) -> None:
        """
        Initialize verifier.

        Args:
            logger: Logger instance.
        """
        self.logger = logger
        self.container_runtime: ContainerRuntime | None = None
        self.compose_tool: ComposeTool | None = None

    def verify_all(self, compose_file: Path) -> bool:
        """
        Verify all prerequisites.

        Args:
            compose_file: Path to docker-compose.yml.

        Returns:
            True if all prerequisites met.
        """
        self.logger.section("Verifying Prerequisites")

        checks = [
            ("Container Runtime", self.verify_container_runtime),
            ("Compose Tool", self.verify_compose_tool),
            ("curl command", lambda: self.verify_command("curl")),
            ("Compose Configuration", lambda: self.verify_compose(compose_file)),
        ]

        all_passed = True
        for name, check_fn in checks:
            try:
                if check_fn():
                    self.logger.ok(f"{name} verified")
                else:
                    self.logger.warn(f"{name} check failed")
                    all_passed = False
            except Exception as e:
                self.logger.error(f"{name} check error: {e}")
                all_passed = False

        return all_passed

    def verify_container_runtime(self) -> bool:
        """Detect and verify container runtime."""
        try:
            self.container_runtime = RuntimeDetector.detect()
            self.logger.debug(
                f"Detected: {self.container_runtime.pretty_name}"
            )
            return True
        except RuntimeError as e:
            self.logger.error(str(e))
            return False

    def verify_compose_tool(self) -> bool:
        """Detect and verify compose tool."""
        try:
            self.compose_tool = ComposeToolDetector.detect()
            self.logger.debug(f"Using: {self.compose_tool.pretty_name}")
            return True
        except RuntimeError as e:
            self.logger.error(str(e))
            return False

    def verify_command(self, command: str) -> bool:
        """Check if command exists."""
        if Command.exists(command):
            return True
        self.logger.error(f"Command not found: {command}")
        return False

    def verify_compose(self, compose_file: Path) -> bool:
        """Validate compose file."""
        if not self.compose_tool:
            self.logger.warn("Compose tool not detected")
            return False

        if not compose_file.exists():
            self.logger.error(f"Compose file not found: {compose_file}")
            return False

        result = self.compose_tool.validate(compose_file)
        if not result.success:
            self.logger.error("Compose validation failed")
            if result.stderr:
                self.logger.debug(result.stderr)
            return False

        return True
