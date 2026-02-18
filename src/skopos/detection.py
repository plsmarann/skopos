from __future__ import annotations

from typing import Optional

from .models import DetectionResult, ProcessInfo
from .processes import permission_signals

AGENT_KEYWORDS = {
    "openai",
    "chatgpt",
    "codex",
    "claude",
    "anthropic",
    "copilot",
    "cursor",
    "autogen",
    "langchain",
    "crewai",
    "aider",
    "windsurf",
}

MODEL_KEYWORDS = {
    "ollama",
    "llama",
    "llama.cpp",
    "vllm",
    "lmstudio",
    "mistral",
    "stable-diffusion",
    "comfyui",
    "whisper",
    "gpt4all",
    "text-generation-webui",
}

SUSPICIOUS_EXEC_PATHS = (
    "/tmp/",
    "/private/tmp/",
    "/var/tmp/",
    "/users/",
)


def _keyword_hits(command: str, keywords: set[str]) -> list[str]:
    lowered = command.lower()
    return sorted([k for k in keywords if k in lowered])


def _is_unknown_agent(command: str, known_hits: list[str], allowlist: set[str]) -> bool:
    lowered = command.lower()
    agent_like_tokens = ("agent", "assistant", "copilot", "autonomous", "gpt", "llm")

    if any(token in lowered for token in agent_like_tokens):
        if known_hits:
            return False
        if any(token in lowered for token in allowlist):
            return False
        return True

    return False


def _risk_and_reasons(result: DetectionResult) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    proc = result.process

    has_agent_signal = bool(result.ai_agent_keywords or result.model_keywords)

    if has_agent_signal:
        score += 20
        reasons.append("AI/agent runtime keyword detected")

    if result.unknown_agent_execution:
        score += 25
        reasons.append("Unknown agent-like execution")

    if result.permissions:
        if result.permissions.privileged_account:
            score += 25
            reasons.append("Runs with privileged account scope")
        if result.permissions.has_listening_socket:
            score += 15
            reasons.append("Process is listening on network port")
        if result.permissions.macos_entitlements:
            score += 5
            reasons.append("macOS entitlements present")

    executable = (proc.executable or "").lower()
    if executable and any(path in executable for path in SUSPICIOUS_EXEC_PATHS):
        score += 15
        reasons.append("Executable path appears user/temp scoped")

    score = min(score, 100)
    return score, reasons


def _severity(score: int) -> str:
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def detect_agents(
    processes: list[ProcessInfo], allowlist_keywords: Optional[list[str]] = None
) -> list[DetectionResult]:
    allowlist = {k.lower() for k in (allowlist_keywords or [])}
    findings: list[DetectionResult] = []

    for proc in processes:
        agent_hits = _keyword_hits(proc.command, AGENT_KEYWORDS)
        model_hits = _keyword_hits(proc.command, MODEL_KEYWORDS)

        unknown = _is_unknown_agent(proc.command, agent_hits + model_hits, allowlist)
        if not agent_hits and not model_hits and not unknown:
            continue

        result = DetectionResult(
            process=proc,
            ai_agent_keywords=agent_hits,
            model_keywords=model_hits,
            unknown_agent_execution=unknown,
            permissions=permission_signals(proc),
        )

        score, reasons = _risk_and_reasons(result)
        result.risk_score = score
        result.severity = _severity(score)
        result.reasons = reasons
        findings.append(result)

    return sorted(findings, key=lambda item: item.risk_score, reverse=True)
