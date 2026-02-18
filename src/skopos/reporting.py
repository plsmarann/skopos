from __future__ import annotations

import json

from .models import DetectionResult


def _join(values: list[str]) -> str:
    return ", ".join(values) if values else "-"


def format_table(findings: list[DetectionResult]) -> str:
    if not findings:
        return "No active AI agents or model runtimes detected."

    lines: list[str] = []
    header = "SEV  SCORE  PID    USER       AGENTS/MODELS                     PORTS   COMMAND"
    lines.append(header)
    lines.append("-" * len(header))

    for item in findings:
        proc = item.process
        keywords = item.ai_agent_keywords + item.model_keywords
        ports = item.permissions.listening_ports if item.permissions else []

        lines.append(
            f"{item.severity.upper():<4} {item.risk_score:>5}  {proc.pid:<6} {proc.user:<10} "
            f"{_join(keywords)[:32]:<32} {_join(ports):<7} {proc.command[:72]}"
        )

    return "\n".join(lines)


def format_detail(findings: list[DetectionResult]) -> str:
    if not findings:
        return ""

    blocks: list[str] = []
    for item in findings:
        proc = item.process
        permissions = item.permissions
        block = [
            f"[{item.severity.upper()}] PID {proc.pid} ({proc.user})",
            f"Command: {proc.command}",
            f"Executable: {proc.executable or 'unknown'}",
            f"Risk score: {item.risk_score}",
            f"Keywords: {_join(item.ai_agent_keywords + item.model_keywords)}",
            f"Unknown agent execution: {'yes' if item.unknown_agent_execution else 'no'}",
        ]

        if permissions:
            block.extend(
                [
                    f"Permission scope: {permissions.account_scope}",
                    f"Listening ports: {_join(permissions.listening_ports)}",
                    f"macOS entitlements: {_join(permissions.macos_entitlements[:6])}",
                ]
            )

        if item.reasons:
            block.append(f"Reasons: {_join(item.reasons)}")

        blocks.append("\n".join(block))

    return "\n\n".join(blocks)


def format_json(findings: list[DetectionResult]) -> str:
    return json.dumps([f.to_dict() for f in findings], indent=2)
