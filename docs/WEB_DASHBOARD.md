# skopos Web Dashboard

The web dashboard provides a real-time visual interface for monitoring AI agents and model runtimes with live updates and kill switch controls.

## Features

- 🔄 **Live Auto-Refresh**: Updates every 5 seconds automatically
- 📊 **Statistics Dashboard**: Overview of risk distribution
- 🎯 **Kill Switch**: Terminate suspicious processes with confirmation
- 🔍 **Filtering**: Show/hide by severity level
- 📥 **Export**: Download findings as JSON
- 🎨 **Dark Theme**: Easy on the eyes during long monitoring sessions

## Quick Start

```bash
# Start the web server
skopos web

# Custom host/port
skopos web --host 0.0.0.0 --port 9000

# Debug mode
skopos web --debug
```

Then open your browser to: **http://localhost:8080**

## Installation

The web dashboard requires Flask:

```bash
# Install with web dependencies
pip install -e ".[web]"

# Or install Flask manually
pip install flask flask-cors
```

## Interface Overview

### Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│ 🛡️ skopos Dashboard                                 │
├─────────────────────────────────────────────────────┤
│ [Stats: High: 2 | Medium: 15 | Low: 127]  🔄 Live  │
├─────────────────────────────────────────────────────┤
│ SEV  RISK  PID    USER    AGENT    PORTS   ACTION  │
│ 🔴 H  85   8432   root    unknown  -       [KILL]  │
│ 🟡 M  40   13501  user    claude   -       [INFO]  │
└─────────────────────────────────────────────────────┘
```

### Components

**1. Statistics Cards**
- **High Risk**: Processes with score 60+
- **Medium Risk**: Processes with score 30-59
- **Low Risk**: Processes with score 0-29
- **Total Detected**: All agent/model processes found

**2. Status Indicator**
- 🟢 Green: Connected, receiving updates
- 🔴 Red: Error or disconnected
- Countdown timer shows seconds until next refresh

**3. Process Table**
- **Severity**: Color-coded badge (HIGH/MED/LOW)
- **Risk**: Numeric score 0-100
- **PID**: Process ID
- **User**: Account running the process
- **Agents/Models**: Detected keywords
- **Ports**: Network listeners
- **Command**: Process command line
- **Actions**: Info and Kill buttons

**4. Detected AI Agents**
- Shows top 10 most common agents
- Process count for each agent type

## Actions

### Kill Process

1. Click **Kill** button next to a process
2. Review confirmation modal with process details
3. Click **Kill Process** to confirm
4. Dashboard auto-refreshes to show updated state

**Safety Features:**
- Cannot kill PID < 2 (init/system)
- Blocks critical system processes
- Requires explicit confirmation
- Shows clear error messages
- Logs all kill attempts

### Filter by Severity

Use checkboxes to show/hide:
- ☑️ High Severity
- ☑️ Medium Severity
- ☑️ Low Severity

Filters apply instantly without page reload.

### Export Data

Click **Export JSON** to download current findings as JSON file:
```json
{
  "process": { "pid": 8432, "user": "root", ... },
  "severity": "high",
  "risk_score": 85,
  ...
}
```

## API Endpoints

The web dashboard exposes a REST API:

### GET /api/scan
Get current detection results.

**Response:**
```json
{
  "success": true,
  "count": 144,
  "findings": [...]
}
```

### GET /api/stats
Get summary statistics.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total": 144,
    "high": 2,
    "medium": 15,
    "low": 127
  },
  "agents": {
    "claude": 5,
    "codex": 8,
    "ollama": 2
  }
}
```

### POST /api/kill/\<pid\>
Terminate a process by PID.

**Request:**
```json
{
  "confirm": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sent SIGTERM to PID 8432",
  "process": "/tmp/unknown-agent"
}
```

**Error Codes:**
- `400`: Confirmation not provided
- `403`: Permission denied or critical process
- `404`: Process not found
- `500`: Internal error

### GET /POST /api/allowlist
Manage process allowlist.

**Add to allowlist:**
```bash
curl -X POST http://localhost:8080/api/allowlist \
  -H "Content-Type: application/json" \
  -d '{"keyword": "ollama", "action": "add"}'
```

**Remove from allowlist:**
```bash
curl -X POST http://localhost:8080/api/allowlist \
  -H "Content-Type: application/json" \
  -d '{"keyword": "ollama", "action": "remove"}'
```

## Security Considerations

### Access Control

**Default configuration** (localhost only):
```bash
skopos web --host 127.0.0.1 --port 8080
```

**Network accessible** (use with caution):
```bash
skopos web --host 0.0.0.0 --port 8080
```

⚠️ **Warning**: When binding to 0.0.0.0, the dashboard is accessible from any network interface. Only use this in trusted networks.

### Recommendations

1. **Firewall**: Block port 8080 from external networks
2. **VPN**: Access dashboard through VPN only
3. **Reverse Proxy**: Use nginx/Apache with authentication
4. **HTTPS**: Add TLS termination for encryption
5. **Auth**: Implement authentication (future feature)

### Kill Switch Safety

Protected processes:
- PID 0, 1 (kernel, init)
- systemd, launchd
- WindowServer, kernel processes

Requires:
- Explicit confirmation in UI
- POST request with `{"confirm": true}`
- Proper permissions (may need sudo for root processes)

## Integration Examples

### Scripted Monitoring

```python
import requests
import time

while True:
    resp = requests.get("http://localhost:8080/api/stats")
    stats = resp.json()["stats"]

    if stats["high"] > 0:
        print(f"⚠️  {stats['high']} high-risk processes detected!")
        # Send alert, log, etc.

    time.sleep(60)
```

### Auto-Kill Policy

```python
import requests

# Kill all unknown agents with high severity
resp = requests.get("http://localhost:8080/api/scan")
findings = resp.json()["findings"]

for f in findings:
    if f["unknown_agent_execution"] and f["severity"] == "high":
        pid = f["process"]["pid"]
        print(f"Auto-killing unknown agent PID {pid}")

        requests.post(
            f"http://localhost:8080/api/kill/{pid}",
            json={"confirm": True}
        )
```

⚠️ **Caution**: Auto-kill scripts can cause data loss. Test thoroughly.

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8080
lsof -i :8080

# Use different port
skopos web --port 9000
```

### Flask Not Found

```bash
# Install web dependencies
pip install -e ".[web]"
# Or directly
pip install flask flask-cors
```

### Permission Denied (Kill)

To kill root processes:
```bash
sudo skopos web
```

Or allow specific PIDs without sudo (advanced):
```bash
# Linux: Use capabilities
sudo setcap cap_kill+ep $(which skopos)
```

### CORS Errors

If accessing from different domain, CORS is pre-enabled. Check browser console for details.

## Future Enhancements

Planned features:
- 🔐 Authentication (password/token)
- 📈 Historical graphs and trends
- 🔔 Browser notifications for high-severity detections
- 🌐 WebSocket for instant updates (vs polling)
- 📧 Email/Slack/webhook alerts
- 🎛️ Process pause/resume (not just kill)
- 📝 Audit log of all kill actions
- 🎨 Light theme option
- 📱 Mobile-responsive layout

## Comparison: CLI vs Web

| Feature | CLI | Web Dashboard |
|---------|-----|---------------|
| Real-time updates | `watch` mode | Auto-refresh |
| Kill process | Manual `kill` | Click button |
| Export data | `--json` flag | Export button |
| Visualization | Text table | Stats cards |
| Filtering | Command flags | Checkboxes |
| Accessibility | Terminal | Browser |
| Multi-user | ❌ | ✅ (future) |
| Historical data | ❌ | ✅ (future) |

Use CLI for:
- Automation and scripting
- SSH/remote sessions
- Low resource usage
- No GUI environment

Use Web for:
- Interactive monitoring
- Visual analysis
- Team collaboration (future)
- Easier process management
