# skopos Architecture

## Overview

`skopos` is a security-focused CLI tool for detecting and monitoring AI agents and local model runtimes on user devices.

## Core Components

### 1. Process Scanner (`processes.py`)
- Cross-platform process enumeration (macOS, Linux, Windows)
- Executable path resolution
- Permission signal collection:
  - User context (privileged vs user scope)
  - Network listeners (via `lsof`)
  - macOS code-signing entitlements

### 2. Detection Engine (`detection.py`)
- Signature-based detection for known agents/models
- Heuristic detection for unknown agent-like execution
- Risk scoring algorithm:
  - Base: AI/agent keywords (+20)
  - Unknown execution (+25)
  - Privileged account (+25)
  - Network listener (+15)
  - Suspicious paths (+15)
  - macOS entitlements (+5)

### 3. Reporting (`reporting.py`)
- Table format (quick scan overview)
- Detailed format (per-process security analysis)
- JSON format (automation/integration)

### 4. CLI (`cli.py`)
- `scan`: One-time detection scan
- `permissions`: Permission audit mode
- `protect`: Real-time protection with alerts
- `watch`: Continuous monitoring mode

## Detection Strategy

### Known Signatures
Two signature sets:
- **Agent keywords**: openai, chatgpt, claude, anthropic, copilot, cursor, langchain, crewai, autogen, aider, windsurf
- **Model keywords**: ollama, llama, llama.cpp, vllm, lmstudio, mistral, stable-diffusion, comfyui, whisper, gpt4all

### Unknown Agent Detection
Heuristic triggers for agent-like tokens (`agent`, `assistant`, `gpt`, `llm`, etc.) in processes that:
- Don't match known signatures
- Aren't in user allowlist
- Exhibit suspicious characteristics

### Risk Scoring
- **Low (0-29)**: Known agent, standard user context
- **Medium (30-59)**: Unknown agent or privileged context
- **High (60-100)**: Multiple risk factors combined

## Security Model

### Threat Model
Protects against:
- Unknown/unauthorized agent execution
- Agents running with excessive privileges
- Hidden network communication by agents
- Suspicious execution paths (temp directories)

### Out of Scope
- Evasion by rootkit-level hiding
- Kernel-mode execution
- Container/VM-internal processes (depends on host visibility)

## Extension System

Extensions can add:
- Custom signature sets
- Platform-specific detectors
- Alert integrations (Slack, email, webhooks)
- Additional permission signals

See `extensions/` directory for examples.

## Performance

- Process scan: ~50-200ms (typical desktop)
- Permission signals: +10-50ms per process (lsof/codesign)
- Watch mode overhead: Negligible at 10s+ intervals

## Platform Support

| Platform | Process Scan | Permissions | Network | Entitlements |
|----------|--------------|-------------|---------|--------------|
| macOS    | ✅           | ✅          | ✅      | ✅           |
| Linux    | ✅           | ✅          | ✅      | ❌           |
| Windows  | ⚠️ Basic     | ⚠️ Limited  | ❌      | ❌           |

⚠️ = Partial support, may require elevated privileges
