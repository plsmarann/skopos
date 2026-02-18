from __future__ import annotations

import json

from .formatting import bold, dim, risk_color, severity_color
from .models import DetectionResult


def _join(values: list[str]) -> str:
    return ", ".join(values) if values else "-"


def format_table(findings: list[DetectionResult]) -> str:
    if not findings:
        return dim("✓ No active AI agents or model runtimes detected.")

    lines: list[str] = []
    header = bold("SEV  RISK  PID    USER       AGENTS/MODELS                    PORTS  COMMAND")
    lines.append(header)
    lines.append("─" * 88)

    for item in findings:
        proc = item.process
        keywords = item.ai_agent_keywords + item.model_keywords
        ports = item.permissions.listening_ports if item.permissions else []
        sev = severity_color(item.severity)
        risk = risk_color(item.risk_score)
        lines.append(
            f"{sev:<12} {risk:>7}  {proc.pid:<6} {proc.user:<10} "
            f"{_join(keywords)[:32]:<32} {_join(ports):<7} {proc.command[:56]}"
        )

    return "\n".join(lines)


def format_detail(findings: list[DetectionResult]) -> str:
    if not findings:
        return ""

    blocks: list[str] = []
    for item in findings:
        proc = item.process
        permissions = item.permissions
        sev = severity_color(item.severity)
        block = [
            bold(f"[{sev}] PID {proc.pid} ({proc.user})"),
            f"  Command: {dim(proc.command)}",
            f"  Executable: {proc.executable or dim('unknown')}",
            f"  Risk score: {risk_color(item.risk_score)}",
            f"  Keywords: {_join(item.ai_agent_keywords + item.model_keywords)}",
            f"  Unknown agent: {'yes' if item.unknown_agent_execution else 'no'}",
        ]
        if permissions:
            scope_color = severity_color("high" if permissions.privileged_account else "low")
            block.extend(
                [
                    f"  Permission scope: {scope_color}",
                    f"  Listening ports: {_join(permissions.listening_ports) or dim('none')}",
                    f"  macOS entitlements: {_join(permissions.macos_entitlements[:6]) or dim('none')}",
                ]
            )
        if item.reasons:
            block.append(f"  Reasons: {', '.join(item.reasons)}")
        blocks.append("\n".join(block))

    return "\n\n".join(blocks)


def format_json(findings: list[DetectionResult]) -> str:
    return json.dumps([f.to_dict() for f in findings], indent=2)
