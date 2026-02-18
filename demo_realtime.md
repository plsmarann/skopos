# How skopos Detects Changes

## 1. **Real-time Scanning**
Every time you run `skopos scan`, it:
- Queries the current process list via `ps` (Unix) or `wmic` (Windows)
- Analyzes each running process
- Reports only what's **currently active**

## 2. **Watch Mode** (Continuous Monitoring)
```bash
skopos watch --interval 10
```
- Scans every 10 seconds (configurable)
- Shows **only changes**: new processes, removed processes, or changed risk scores
- Perfect for monitoring over time

## 3. **What Changes Get Detected**

### Processes Starting:
If you launch a new AI agent (e.g., open Cursor editor):
- ✅ Next scan will detect it
- ✅ Shows in watch mode immediately

### Processes Stopping:
If you quit an AI agent:
- ✅ Removed from next scan
- ✅ Watch mode shows it disappeared

### Permission Changes:
If a process gains new permissions (e.g., opens a network port):
- ✅ Risk score updates
- ✅ Severity level may change

## 4. **Live Example**

Current detection on your system:
- **Claude**: 5 processes
- **Codex/OpenAI**: 8 processes  
- **Copilot**: 3 processes
- **Cursor**: 1 process
- **Anthropic**: 1 process

If you:
- Close Claude → count drops to 4 or 0
- Start Ollama → new "ollama" entry appears
- Run agent as root → severity jumps from LOW to MEDIUM/HIGH

## 5. **Try It Yourself**

```bash
# Watch in one terminal
skopos watch --interval 5

# In another terminal, start/stop agents
# open -a "Cursor"
# killall claude
# ollama serve
```

You'll see changes appear in real-time!
