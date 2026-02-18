"""Configuration management for skopos."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class SkoposConfig:
    """Skopos configuration."""

    agent_keywords: list[str] = field(default_factory=list)
    model_keywords: list[str] = field(default_factory=list)
    allowlist: list[str] = field(default_factory=list)
    watch_interval: int = 10
    min_severity: str = "low"
    enable_network_detection: bool = True
    enable_entitlements: bool = True
    alert_high_severity: bool = False
    alert_webhook: str | None = None


def _default_config_path() -> Path:
    """Return platform-specific config directory."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", "~")).expanduser()
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    return base / "skopos" / "config.yaml"


def load_config(config_path: str | None = None) -> SkoposConfig:
    """Load configuration from file."""
    path = Path(config_path) if config_path else _default_config_path()

    if not path.exists():
        return SkoposConfig()

    if not HAS_YAML:
        return SkoposConfig()

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return SkoposConfig()

    return SkoposConfig(
        agent_keywords=data.get("agent_keywords", []),
        model_keywords=data.get("model_keywords", []),
        allowlist=data.get("allowlist", []),
        watch_interval=data.get("watch_interval", 10),
        min_severity=data.get("min_severity", "low"),
        enable_network_detection=data.get("enable_network_detection", True),
        enable_entitlements=data.get("enable_entitlements", True),
        alert_high_severity=data.get("alert_high_severity", False),
        alert_webhook=data.get("alert_webhook"),
    )


def save_config(config: SkoposConfig, config_path: str | None = None) -> None:
    """Save configuration to file."""
    if not HAS_YAML:
        raise RuntimeError("PyYAML required for config save: pip install pyyaml")

    path = Path(config_path) if config_path else _default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "agent_keywords": config.agent_keywords,
        "model_keywords": config.model_keywords,
        "allowlist": config.allowlist,
        "watch_interval": config.watch_interval,
        "min_severity": config.min_severity,
        "enable_network_detection": config.enable_network_detection,
        "enable_entitlements": config.enable_entitlements,
        "alert_high_severity": config.alert_high_severity,
        "alert_webhook": config.alert_webhook,
    }

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False)
