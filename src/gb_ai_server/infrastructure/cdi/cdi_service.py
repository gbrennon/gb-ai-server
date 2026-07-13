"""CDI (Container Device Interface) operations.

Responsible for checking, enabling, and verifying CDI for GPU passthrough.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

from ..command import Command
from ..logging import TerminalLogger


@dataclass
class CdiStatus:
    active: bool = False
    devices: list[str] = field(default_factory=list)
    error: str | None = None


class CdiService:
    """Container Device Interface operations for GPU passthrough."""

    def __init__(self, logger: TerminalLogger) -> None:
        self._logger = logger

    def check(self) -> CdiStatus:
        """Check if CDI is active via ``nvidia-ctk cdi list``."""
        if not Command.exists("nvidia-ctk"):
            return CdiStatus(active=False, error="nvidia-ctk not found")

        try:
            result = subprocess.run(
                ["nvidia-ctk", "cdi", "list"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return CdiStatus(
                    active=False,
                    error=result.stderr.strip() or "nvidia-ctk cdi list failed",
                )
            devices = [
                line.strip()
                for line in result.stdout.strip().splitlines()
                if line.strip() and not line.startswith("time=")
            ]
            return CdiStatus(active=True, devices=devices)
        except FileNotFoundError:
            return CdiStatus(active=False, error="nvidia-ctk not found")
        except subprocess.TimeoutExpired:
            return CdiStatus(active=False, error="nvidia-ctk timed out")

    def enable(self) -> CdiStatus:
        """Generate CDI specs via ``nvidia-ctk cdi generate``."""
        if not Command.exists("nvidia-ctk"):
            return CdiStatus(active=False, error="nvidia-ctk not found")

        try:
            result = subprocess.run(
                ["nvidia-ctk", "cdi", "generate"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return CdiStatus(
                    active=False,
                    error=result.stderr.strip() or "nvidia-ctk cdi generate failed",
                )
            self._logger.ok("CDI specs generated")
            return self.check()
        except FileNotFoundError:
            return CdiStatus(active=False, error="nvidia-ctk not found")
        except subprocess.TimeoutExpired:
            return CdiStatus(active=False, error="nvidia-ctk cdi generate timed out")

    def ensure(self) -> CdiStatus:
        """Check CDI; auto-enable if missing; return final status."""
        status = self.check()
        if status.active:
            self._logger.ok("CDI is active")
            return status

        self._logger.warn(
            f"CDI not active{' — ' + status.error if status.error else ''}"
        )
        self._logger.info("Attempting to enable CDI...")
        status = self.enable()

        if status.active:
            self._logger.ok("CDI enabled successfully")
        else:
            self._logger.warn(
                f"Could not enable CDI{' — ' + status.error if status.error else ''}. "
                "GPU passthrough may not work. Run with CPU-only or install "
                "nvidia-container-toolkit."
            )
        return status

    def check_nvidia_smi(self) -> bool:
        """Check if an NVIDIA GPU is visible via ``nvidia-smi``."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "-L"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
