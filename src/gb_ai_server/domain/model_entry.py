"""Model entry domain logic."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelEntry:
    """
    Immutable model specification entry.

    Format: "display_name|filename|download_url"
    """

    display_name: str
    filename: str
    url: str

    @classmethod
    def from_string(cls, entry: str) -> "ModelEntry":
        """
        Parse model entry from pipe-delimited string.

        Args:
            entry: String in format "display_name|filename|url"

        Returns:
            ModelEntry instance.

        Raises:
            ValueError: If entry format is invalid.
        """
        parts = entry.split("|")
        if len(parts) != 3:
            msg = (
                f"Invalid model entry format: {entry}. "
                "Expected: display_name|filename|url"
            )
            raise ValueError(msg)

        display_name, filename, url = parts
        if not all([display_name, filename, url]):
            raise ValueError("Model entry contains empty fields")

        return cls(
            display_name=display_name.strip(),
            filename=filename.strip(),
            url=url.strip(),
        )

    @classmethod
    def from_tuple(cls, entry: tuple[str, str, str]) -> "ModelEntry":
        """
        Create ModelEntry from tuple.

        Args:
            entry: Tuple of (display_name, filename, url)

        Returns:
            ModelEntry instance.
        """
        return cls(
            display_name=entry[0],
            filename=entry[1],
            url=entry[2],
        )

    def __str__(self) -> str:
        """Serialize to pipe-delimited format."""
        return f"{self.display_name}|{self.filename}|{self.url}"
