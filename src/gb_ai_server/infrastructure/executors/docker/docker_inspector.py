"""Docker container inspector adapter."""

from ....application.ports.outbound import ContainerInspector
from ...command import Command, CommandResult


class DockerInspector(ContainerInspector):
    """Inspect Docker containers."""

    def is_running(self, container_name: str) -> bool:
        result = Command.run(
            "docker",
            "inspect",
            "-f",
            "{{.State.Running}}",
            container_name,
            capture_output=True,
        )
        return result.success and result.stdout.strip() == "true"

    def get_env(self, container_name: str, var_name: str) -> str | None:
        result = Command.run(
            "docker",
            "inspect",
            "-f",
            '{{range .Config.Env}}{{println .}}{{end}}',
            container_name,
            capture_output=True,
        )
        if not result.success:
            return None
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, val = line.split("=", 1)
                if key == var_name:
                    return val
        return None

    def ps(self) -> CommandResult:
        return Command.run("docker", "ps", capture_output=True)

    def logs(self, container_name: str, follow: bool = False) -> CommandResult:
        args = ["docker", "logs"]
        if follow:
            args.append("-f")
        args.append(container_name)
        return Command.run(*args, capture_output=True)
