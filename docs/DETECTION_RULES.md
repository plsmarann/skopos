# Detection Rules

## Built-in Signatures

### AI Agent Platforms
- **OpenAI**: openai, chatgpt, codex, gpt-4
- **Anthropic**: claude, anthropic
- **GitHub**: copilot, github-copilot-agent
- **Cursor**: cursor, cursor-ai
- **Aider**: aider, aider-chat
- **Windsurf**: windsurf, codeium
- **Agent Frameworks**: autogen, crewai, langchain, semantic-kernel

### Local Model Runtimes
- **Ollama**: ollama
- **llama.cpp**: llama.cpp, llama-server
- **vLLM**: vllm
- **LM Studio**: lmstudio
- **GPT4All**: gpt4all
- **ComfyUI**: comfyui
- **Stable Diffusion**: stable-diffusion, automatic1111
- **Whisper**: whisper, faster-whisper
- **Text Generation WebUI**: text-generation-webui, oobabooga

## Risk Scoring Logic

### Base Score (Process Classification)
- Known agent/model keyword detected: **+20**
- Unknown agent-like execution: **+25**

### Permission Amplifiers
- Privileged account (root/SYSTEM): **+25**
- Network listener active: **+15**
- Suspicious execution path: **+15**
- macOS entitlements present: **+5**

### Severity Thresholds
- **Low (0-29)**: Standard agent execution, user scope
- **Medium (30-59)**: Elevated risk (privileged or unknown)
- **High (60+)**: Multiple high-risk factors

## Examples

### Example 1: Known Agent, Safe Context
```
Process: /usr/local/bin/ollama serve
User: regular_user
Listening: :11434
Score: 20 (agent) + 15 (network) = 35 → Medium
```

### Example 2: Unknown Agent, Privileged
```
Process: /tmp/mystery-agent --daemon
User: root
Score: 25 (unknown) + 25 (privileged) + 15 (tmp path) = 65 → High
```

### Example 3: Known Agent, System Scope
```
Process: /Applications/Cursor.app/Contents/MacOS/cursor
User: root (unusual for IDE)
Score: 20 (agent) + 25 (privileged) = 45 → Medium
```

## Allowlist Behavior

Use `--allow <keyword>` to mark known-safe agents:
```bash
skopos scan --allow ollama --allow cursor
```

Allowlisted keywords bypass unknown agent detection but still contribute to risk scoring for visibility.

## Custom Signatures

Create extension files in `~/.config/skopos/signatures/`:

```yaml
# ~/.config/skopos/signatures/custom.yaml
agent_keywords:
  - my-internal-agent
  - company-copilot

model_keywords:
  - custom-llm-server

allowlist:
  - safe-automation-tool
```

Load with:
```bash
skopos scan --signatures ~/.config/skopos/signatures/custom.yaml
```
