"""Shared utilities for application layer services."""


def print_section(title: str) -> None:
    """Print a section header with separator lines to stdout."""
    separator = "\u2500" * (len(title) + 4)
    print(f"\n{separator}")
    print(f" {title}")
    print(f"{separator}")
