# 🛡️ skopos

> **σκοπός** (skopos): Ancient Greek for "scout" or "look-out"

A security-focused CLI guardian that detects and monitors AI agents and local model runtimes on your device. Know what's running, protect against unknown execution, and understand permission scope.

[![CI](https://github.com/plsmarann/skopos/workflows/CI/badge.svg)](https://github.com/plsmarann/skopos/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why skopos?

Modern AI agents can:
- Run as background daemons
- Execute with elevated privileges
- Open network listeners
- Operate without clear user visibility

**skopos gives you visibility:**
- 🔍 Detect known AI agents (Claude, Copilot, Cursor, Ollama, etc.)
- ⚠️ Flag unknown agent-like execution
- 🔐 Report permission scope (privileged accounts, network access)
- 📊 Risk scoring and severity classification
- 🎯 Real-time protection mode with alerts

## Quick Start

### Install
```bash
# From source
git clone https://github.com/plsmarann/skopos.git
cd skopos
./scripts/install.sh

# Or with pip (editable)
pip install -e .
```

### Basic Usage
```bash
# Quick scan
skopos scan

# Detailed security analysis
skopos scan --detailed

# JSON output for automation
skopos scan --json

# Real-time protection
skopos protect --min-severity medium

# Continuous monitoring
skopos watch --interval 10
```

### Example Output
```
SEV  RISK  PID    USER       AGENTS/MODELS                    PORTS  COMMAND
────────────────────────────────────────────────────────────────────────────────
MED    35  12847  user       ollama                           11434  /usr/local/bin/ollama serve
HIGH   65  8432   root       -                                -      /tmp/unknown-agent --daemon
LOW    20  19284  user       cursor                           -      /Applications/Cursor.app/Contents/MacOS/Cursor
```

## Commands

| Command | Description |
|---------|-------------|
| `skopos scan` | One-time detection scan |
| `skopos permissions` | Audit agent permission scope |
| `skopos protect` | Real-time protection with alerts |
| `skopos watch` | Continuous monitoring mode |

### Common Flags
- `--allow <keyword>`: Allowlist known-safe agents
- `--json`: Machine-readable JSON output
- `--detailed`: Show per-process security details
- `--min-severity <level>`: Filter by severity (low/medium/high)

## Detection Coverage

### Known AI Agents
OpenAI, ChatGPT, Claude, Anthropic, GitHub Copilot, Cursor, Aider, Windsurf, AutoGen, CrewAI, LangChain, and more.

### Local Model Runtimes
Ollama, llama.cpp, vLLM, LM Studio, GPT4All, Stable Diffusion, ComfyUI, Whisper, Text Generation WebUI, and more.

See [DETECTION_RULES.md](docs/DETECTION_RULES.md) for complete signature list.

## Configuration

Create `~/.config/skopos/config.yaml`:
```yaml
allowlist:
  - ollama
  - cursor
min_severity: medium
watch_interval: 10
alert_high_severity: true
alert_webhook: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Security Model

### Risk Scoring
- **Known agent/model keyword**: +20
- **Unknown agent-like execution**: +25
- **Privileged account (root/SYSTEM)**: +25
- **Network listener active**: +15
- **Suspicious execution path**: +15
- **macOS entitlements present**: +5

### Severity Levels
- **Low (0-29)**: Standard execution, user scope
- **Medium (30-59)**: Elevated risk (unknown or privileged)
- **High (60+)**: Multiple high-risk factors

### Out of Scope
- Rootkit-level hiding
- Kernel-mode execution
- Container/VM-internal processes (depends on host visibility)

## Platform Support

| Platform | Process Detection | Permission Signals | Network Listeners | Code Signing |
|----------|-------------------|-------------------|-------------------|--------------|
| macOS    | ✅                | ✅                | ✅                | ✅           |
| Linux    | ✅                | ✅                | ✅                | ❌           |
| Windows  | ⚠️ Basic          | ⚠️ Limited        | ❌                | ❌           |

## Development

```bash
# Setup dev environment
./scripts/dev-setup.sh

# Run tests
pytest

# Format code
black src tests

# Lint
ruff check src tests

# Type check
mypy src
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Detection Rules](docs/DETECTION_RULES.md)

## Contributing

Contributions welcome! Please open an issue or PR.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Inspired by [openclaw](https://github.com/openclaw/openclaw) - security tooling with minimal dependencies and maximum clarity.
