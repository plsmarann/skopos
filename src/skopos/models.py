from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class PermissionSignals:
    privileged_account: bool
    account_scope: str
    has_listening_socket: bool
    listening_ports: list[str] = field(default_factory=list)
    macos_entitlements: list[str] = field(default_factory=list)


@dataclass
class ProcessInfo:
    pid: int
    ppid: int
    user: str
    cpu_percent: float
    mem_percent: float
    command: str
    executable: Optional[str]


@dataclass
class DetectionResult:
    process: ProcessInfo
    ai_agent_keywords: list[str] = field(default_factory=list)
    model_keywords: list[str] = field(default_factory=list)
    unknown_agent_execution: bool = False
    permissions: Optional[PermissionSignals] = None
    risk_score: int = 0
    severity: str = "low"
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.permissions is None:
            payload["permissions"] = None
        return payload
