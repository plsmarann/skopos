"""Custom detection rules for skopos."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .models import DetectionResult, ProcessInfo


@dataclass
class DetectionRule:
    """A custom detection rule."""

    name: str
    description: str
    enabled: bool = True

    # Match conditions
    command_pattern: Optional[str] = None
    user_pattern: Optional[str] = None
    path_pattern: Optional[str] = None

    # Keywords
    required_keywords: list[str] = field(default_factory=list)
    excluded_keywords: list[str] = field(default_factory=list)

    # Risk scoring
    risk_modifier: int = 0  # Add to base risk score
    severity_override: Optional[str] = None  # Override severity

    # Actions
    auto_kill: bool = False
    alert: bool = False

    def matches(self, process: ProcessInfo) -> bool:
        """Check if process matches this rule."""
        # Check command pattern
        if self.command_pattern:
            if not re.search(self.command_pattern, process.command, re.IGNORECASE):
                return False

        # Check user pattern
        if self.user_pattern:
            if not re.search(self.user_pattern, process.user, re.IGNORECASE):
                return False

        # Check path pattern
        if self.path_pattern and process.executable:
            if not re.search(self.path_pattern, process.executable, re.IGNORECASE):
                return False

        # Check required keywords
        if self.required_keywords:
            command_lower = process.command.lower()
            if not all(kw.lower() in command_lower for kw in self.required_keywords):
                return False

        # Check excluded keywords
        if self.excluded_keywords:
            command_lower = process.command.lower()
            if any(kw.lower() in command_lower for kw in self.excluded_keywords):
                return False

        return True

    def apply(self, result: DetectionResult) -> DetectionResult:
        """Apply this rule to a detection result."""
        # Modify risk score
        if self.risk_modifier:
            result.risk_score = max(0, min(100, result.risk_score + self.risk_modifier))

        # Override severity
        if self.severity_override:
            result.severity = self.severity_override

        # Add rule name to reasons
        result.reasons.append(f"Matched custom rule: {self.name}")

        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "command_pattern": self.command_pattern,
            "user_pattern": self.user_pattern,
            "path_pattern": self.path_pattern,
            "required_keywords": self.required_keywords,
            "excluded_keywords": self.excluded_keywords,
            "risk_modifier": self.risk_modifier,
            "severity_override": self.severity_override,
            "auto_kill": self.auto_kill,
            "alert": self.alert,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DetectionRule:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            enabled=data.get("enabled", True),
            command_pattern=data.get("command_pattern"),
            user_pattern=data.get("user_pattern"),
            path_pattern=data.get("path_pattern"),
            required_keywords=data.get("required_keywords", []),
            excluded_keywords=data.get("excluded_keywords", []),
            risk_modifier=data.get("risk_modifier", 0),
            severity_override=data.get("severity_override"),
            auto_kill=data.get("auto_kill", False),
            alert=data.get("alert", False),
        )


class RuleManager:
    """Manages custom detection rules."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".config" / "skopos"
        self.rules_file = self.config_dir / "rules.json"
        self.rules: dict[str, DetectionRule] = {}
        self._load()

    def _load(self) -> None:
        """Load rules from config file."""
        if not self.rules_file.exists():
            self._create_default_rules()
            return

        try:
            with open(self.rules_file, encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    rule = DetectionRule.from_dict(item)
                    self.rules[rule.name] = rule
        except Exception as e:
            print(f"Error loading rules: {e}")
            self._create_default_rules()

    def _create_default_rules(self) -> None:
        """Create default example rules."""
        self.rules = {
            "high-risk-temp-execution": DetectionRule(
                name="high-risk-temp-execution",
                description="Agents running from temp directories",
                path_pattern=r"/(tmp|temp)/",
                risk_modifier=30,
                severity_override="high",
                alert=True,
            ),
            "root-agent": DetectionRule(
                name="root-agent",
                description="AI agents running as root",
                user_pattern=r"^root$",
                required_keywords=["agent", "ai"],
                risk_modifier=25,
                alert=True,
            ),
            "suspicious-network-agent": DetectionRule(
                name="suspicious-network-agent",
                description="Agents with suspicious network behavior",
                required_keywords=["agent"],
                risk_modifier=20,
                alert=True,
            ),
        }
        self.save()

    def save(self) -> None:
        """Save rules to config file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        data = [r.to_dict() for r in self.rules.values()]
        with open(self.rules_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add(self, rule: DetectionRule) -> None:
        """Add or update a rule."""
        self.rules[rule.name] = rule
        self.save()

    def remove(self, name: str) -> bool:
        """Remove a rule."""
        if name in self.rules:
            del self.rules[name]
            self.save()
            return True
        return False

    def get(self, name: str) -> Optional[DetectionRule]:
        """Get a rule by name."""
        return self.rules.get(name)

    def list(self) -> list[DetectionRule]:
        """List all rules."""
        return list(self.rules.values())

    def apply_rules(
        self, process: ProcessInfo, result: DetectionResult
    ) -> DetectionResult:
        """Apply all matching rules to a detection result."""
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if rule.matches(process):
                result = rule.apply(result)

        return result
