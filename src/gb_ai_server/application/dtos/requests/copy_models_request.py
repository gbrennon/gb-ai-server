"""Request DTO for copying models to container."""


class CopyModelsRequest:
    """Request to copy model files into a running container."""

    def __init__(
        self,
        entries: list[tuple[str, str, str]],
        source_dir: str,
        container_name: str,
        dest_dir: str = "/models",
    ) -> None:
        self.entries = entries
        self.source_dir = source_dir
        self.container_name = container_name
        self.dest_dir = dest_dir
