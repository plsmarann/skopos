# skopos

`skopos` (Greek: scout/look-out) is a local CLI guardian that scans your machine for AI agents and local model runtimes, highlights unknown executions, and reports likely permission scope.

## Why this exists

Modern agentic tools can run background processes, call local models, and open network listeners. `skopos` gives a quick local view of:

- Known AI agents and model runtimes currently running
- Potentially unknown agent-like processes
- Permission posture (user/root context, entitlement hints, listening ports)

## Install (editable)

```bash
cd /Users/plkhadka/new
python3 -m pip install --no-build-isolation -e .
```

## Usage

Run one-time scan:

```bash
skopos scan
```

Permissions-focused report:

```bash
skopos permissions
```

Protection recommendations (triage mode):

```bash
skopos protect --min-severity medium
```

JSON output for automation:

```bash
skopos scan --json
```

Allowlist safe keywords and reduce noise:

```bash
skopos scan --allow ollama --allow claude
```

Continuous watch mode:

```bash
skopos watch --interval 10
```

## Scope and limits

- This is a heuristic detector, not an EDR product.
- Permission reporting is inferred from process context and local signals.
- Runtime behavior and hidden code execution can evade basic process inspection.

## Safety model

`skopos` labels a process with risk signals when it sees combinations like:

- Agent/model keyword + elevated account (`root`/`SYSTEM`)
- Agent-like process unknown to built-in signatures
- Active listening sockets on agent/model process
- Suspicious execution path (for example `/tmp`)

Use these signals for triage, then investigate manually.
