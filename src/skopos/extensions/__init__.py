"""Extension system for custom detectors and signatures."""

from __future__ import annotations

__all__ = ["Extension", "load_extensions"]


class Extension:
    """Base class for skopos extensions."""

    name: str = "base"
    version: str = "0.1.0"

    def agent_keywords(self) -> list[str]:
        """Return custom agent keywords."""
        return []

    def model_keywords(self) -> list[str]:
        """Return custom model keywords."""
        return []

    def detect(self, process: "ProcessInfo") -> dict[str, object] | None:  # noqa: F821
        """Custom detection logic. Return dict with findings or None."""
        return None


def load_extensions(extension_dir: str | None = None) -> list[Extension]:
    """Load extensions from directory."""
    # TODO: Implement dynamic extension loading
    return []
