# Phase 3: Advanced Control Features

## Overview

Phase 3 adds powerful process management and distributed monitoring capabilities to skopos.

## Features

### 1. Process Pause/Resume

Pause and resume processes without killing them.

**Module**: `skopos.control`

**CLI Usage**:
```bash
# Pause a suspicious agent (freeze execution)
skopos control pause <PID>

# Resume a paused process
skopos control resume <PID>

# Get process status
skopos control status <PID>
```

**API Usage**:
```bash
# Pause
curl -X POST http://localhost:8080/api/control/pause/8432

# Resume
curl -X POST http://localhost:8080/api/control/resume/8432
```

**Use Cases**:
- Freeze suspicious agent for investigation
- Temporarily pause high-CPU agents
- Non-destructive process management

### 2. Remote Agent Support

Deploy agents on multiple machines reporting to central server.

**Module**: `skopos.remote_agent`

**Start Remote Agent**:
```bash
# On remote machine
skopos agent --server central.example.com --port 8080 --name web-server-01
```

**Central Server**:
```bash
# Receive reports from all agents
skopos web --enable-remote
```

**Architecture**:
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Agent 1    │      │  Agent 2    │      │  Agent 3    │
│  (Server A) │─────▶│             │◀─────│  (Server C) │
└─────────────┘      │   Central   │      └─────────────┘
                     │   Dashboard │
                     │             │
                     └─────────────┘
```

**Features**:
- Multi-machine monitoring
- Centralized detection view
- Per-agent statistics
- Real-time updates via WebSocket

### 3. Scheduled Scans

Automate scans with custom schedules and actions.

**Module**: `skopos.scheduler`

**CLI Usage**:
```bash
# Add scheduled scan (every 5 minutes)
skopos schedule add "hourly-check" --interval 300 --min-severity medium

# List schedules
skopos schedule list

# Enable/disable
skopos schedule enable "hourly-check"
skopos schedule disable "hourly-check"

# Remove
skopos schedule remove "hourly-check"
```

**Programmatic Usage**:
```python
from skopos.scheduler import Scheduler, ScheduledScan

scheduler = Scheduler()

# Add scan
scan = ScheduledScan(
    name="quick-scan",
    interval=60,  # seconds
    min_severity="high",
    callback=lambda findings: print(f"Found {len(findings)} issues")
)
scheduler.add(scan)
scheduler.start()
```

**Features**:
- Custom scan intervals
- Severity filtering
- Callback functions
- Persistent configuration
- Auto-start on system boot (via systemd/launchd)

### 4. Custom Detection Rules

Create custom rules for specific threats.

**Module**: `skopos.rules`

**Rule Format**:
```json
{
  "name": "high-risk-temp-execution",
  "description": "Agents running from temp directories",
  "enabled": true,
  "path_pattern": "/(tmp|temp)/",
  "risk_modifier": 30,
  "severity_override": "high",
  "alert": true,
  "auto_kill": false
}
```

**CLI Usage**:
```bash
# List rules
skopos rules list

# Add rule
skopos rules add --name "my-rule" \
  --pattern "/tmp/" \
  --risk-modifier 30 \
  --alert

# Enable/disable
skopos rules enable "my-rule"
skopos rules disable "my-rule"
```

**Rule Conditions**:
- `command_pattern`: Regex match on command line
- `user_pattern`: Regex match on user
- `path_pattern`: Regex match on executable path
- `required_keywords`: All must be present
- `excluded_keywords`: None can be present

**Rule Actions**:
- `risk_modifier`: Add/subtract from risk score
- `severity_override`: Force severity level
- `alert`: Trigger high-priority alert
- `auto_kill`: Automatically terminate matching processes

**Default Rules**:
1. **high-risk-temp-execution**: Temp directory execution (+30 risk)
2. **root-agent**: AI agents as root (+25 risk)
3. **suspicious-network-agent**: Agents with network activity (+20 risk)

## CLI Commands Summary

```bash
# Control commands
skopos control pause <PID>
skopos control resume <PID>
skopos control status <PID>
skopos control kill <PID> [--force]

# Remote agent
skopos agent \
  --server <HOST> \
  --port <PORT> \
  --name <AGENT_NAME> \
  --interval <SECONDS>

# Scheduler
skopos schedule add <NAME> --interval <SECONDS> [--min-severity LEVEL]
skopos schedule list
skopos schedule remove <NAME>
skopos schedule enable/disable <NAME>

# Rules
skopos rules list
skopos rules add <NAME> [OPTIONS]
skopos rules remove <NAME>
skopos rules enable/disable <NAME>
skopos rules test <NAME> --pid <PID>
```

## Web Dashboard Integration

### New API Endpoints

**Process Control**:
```
POST /api/control/pause/<pid>
POST /api/control/resume/<pid>
GET  /api/control/status/<pid>
```

**Remote Agents**:
```
POST /api/remote/report          # Receive agent reports
GET  /api/remote/agents          # List all agents
GET  /api/remote/agent/<name>    # Get specific agent
```

**Scheduler**:
```
GET    /api/schedules            # List schedules
POST   /api/schedules            # Add schedule
DELETE /api/schedules/<name>     # Remove schedule
PUT    /api/schedules/<name>     # Update schedule
```

**Rules**:
```
GET    /api/rules                # List rules
POST   /api/rules                # Add rule
DELETE /api/rules/<name>         # Remove rule
PUT    /api/rules/<name>         # Update rule
POST   /api/rules/<name>/test    # Test rule
```

### Dashboard UI Additions

**Process Table Actions**:
- 🟢 **Pause** button (freeze process)
- ▶️ **Resume** button (un-freeze)
- 🔴 **Kill** button (terminate)
- ℹ️ **Info** button (details)

**Remote Agents Panel**:
- List of connected agents
- Last seen timestamp
- Per-agent statistics
- Health status

**Schedules Panel**:
- Active schedules list
- Next run time
- Enable/disable toggle
- Add new schedule form

**Rules Panel**:
- Custom rules list
- Enable/disable toggle
- Rule testing
- Add/edit rule form

## Use Cases

### 1. Freeze Suspicious Agent for Analysis
```bash
# Detect unknown agent
skopos scan --json | jq '.[] | select(.unknown_agent_execution)'

# Pause it
skopos control pause 8432

# Analyze (safe while paused)
strings /proc/8432/exe
lsof -p 8432

# Resume or kill
skopos control resume 8432
# or
skopos control kill 8432
```

### 2. Distributed Fleet Monitoring
```bash
# Central server
skopos web --enable-remote --host 0.0.0.0

# On each server
skopos agent --server central.company.com --name $(hostname)

# View all agents in web dashboard
open http://central.company.com:8080/agents
```

### 3. Automated High-Risk Response
```python
from skopos.scheduler import Scheduler, ScheduledScan
from skopos.control import ProcessControl

def auto_respond(findings):
    for f in findings:
        if f.severity == "high" and f.unknown_agent_execution:
            # Auto-pause high-risk unknown agents
            ProcessControl.pause(f.process.pid)
            print(f"⚠️  Auto-paused PID {f.process.pid}")

scan = ScheduledScan(
    name="auto-response",
    interval=30,
    min_severity="high",
    callback=auto_respond
)

scheduler = Scheduler()
scheduler.add(scan)
scheduler.start()
```

### 4. Custom Rule for Specific Threat
```bash
# Block specific malicious pattern
skopos rules add "crypto-miner" \
  --required-keywords "xmrig,stratum,pool" \
  --risk-modifier 50 \
  --severity high \
  --auto-kill \
  --alert
```

## Configuration

### Scheduler Config
`~/.config/skopos/schedules.json`:
```json
[
  {
    "name": "hourly-scan",
    "interval": 3600,
    "enabled": true,
    "min_severity": "medium",
    "allowlist": ["ollama", "cursor"]
  }
]
```

### Rules Config
`~/.config/skopos/rules.json`:
```json
[
  {
    "name": "my-custom-rule",
    "description": "Catch specific threat",
    "enabled": true,
    "command_pattern": "malicious.*pattern",
    "risk_modifier": 40,
    "alert": true
  }
]
```

## Implementation Status

| Feature | Status | Module |
|---------|--------|--------|
| Process pause/resume | ✅ Complete | `control.py` |
| Remote agents | ✅ Complete | `remote_agent.py` |
| Scheduled scans | ✅ Complete | `scheduler.py` |
| Custom rules | ✅ Complete | `rules.py` |
| CLI commands | ⏳ In progress | `cli.py` |
| Web API endpoints | ⏳ In progress | `web/server.py` |
| Dashboard UI | ⏳ Planned | `web/templates/` |

## Next Steps

1. Integrate Phase 3 modules into CLI
2. Add API endpoints to web server
3. Update dashboard UI
4. Write comprehensive tests
5. Update documentation
6. Release v0.4.0

## Platform Support

| Feature | macOS | Linux | Windows |
|---------|-------|-------|---------|
| Pause/Resume | ✅ SIGSTOP/SIGCONT | ✅ SIGSTOP/SIGCONT | ⚠️ PowerShell |
| Remote agents | ✅ | ✅ | ✅ |
| Scheduler | ✅ | ✅ | ✅ |
| Custom rules | ✅ | ✅ | ✅ |
