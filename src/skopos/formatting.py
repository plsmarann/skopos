"""Terminal formatting utilities."""

from __future__ import annotations

import sys

# Color support detection
_FORCE_COLOR = False
_NO_COLOR = False


def _supports_color() -> bool:
    """Detect terminal color support."""
    if _NO_COLOR:
        return False
    if _FORCE_COLOR:
        return True
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    return True


USE_COLOR = _supports_color()


def red(text: str) -> str:
    """Red text."""
    return f"\033[31m{text}\033[0m" if USE_COLOR else text


def yellow(text: str) -> str:
    """Yellow text."""
    return f"\033[33m{text}\033[0m" if USE_COLOR else text


def green(text: str) -> str:
    """Green text."""
    return f"\033[32m{text}\033[0m" if USE_COLOR else text


def blue(text: str) -> str:
    """Blue text."""
    return f"\033[34m{text}\033[0m" if USE_COLOR else text


def bold(text: str) -> str:
    """Bold text."""
    return f"\033[1m{text}\033[0m" if USE_COLOR else text


def dim(text: str) -> str:
    """Dimmed text."""
    return f"\033[2m{text}\033[0m" if USE_COLOR else text


def severity_color(severity: str) -> str:
    """Color code severity level."""
    if severity == "high":
        return red("HIGH")
    if severity == "medium":
        return yellow("MED")
    return green("LOW")


def risk_color(score: int) -> str:
    """Color code risk score."""
    if score >= 60:
        return red(str(score))
    if score >= 30:
        return yellow(str(score))
    return green(str(score))
