from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Optional

from .detection import detect_agents
from .processes import list_processes
from .reporting import format_detail, format_json, format_table


def _scan(allowlist: list[str], as_json: bool, detailed: bool) -> int:
    processes = list_processes()
    findings = detect_agents(processes, allowlist_keywords=allowlist)

    if as_json:
        print(format_json(findings))
        return 0

    print(format_table(findings))
    if detailed and findings:
        print()
        print(format_detail(findings))

    return 0 if findings else 1


def _watch(allowlist: list[str], interval: int) -> int:
    print(f"Starting skopos watch mode ({interval}s interval). Press Ctrl+C to stop.")
    previous: dict[int, tuple[int, str]] = {}

    try:
        while True:
            findings = detect_agents(list_processes(), allowlist_keywords=allowlist)
            current = {f.process.pid: (f.risk_score, f.process.command) for f in findings}

            added = [pid for pid in current if pid not in previous]
            removed = [pid for pid in previous if pid not in current]
            changed = [pid for pid in current if pid in previous and current[pid] != previous[pid]]

            if added or removed or changed:
                print("\n=== skopos update ===")
                print(format_table(findings))

            previous = current
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


def _permissions(allowlist: list[str], as_json: bool) -> int:
    findings = detect_agents(list_processes(), allowlist_keywords=allowlist)
    payload = []
    for item in findings:
        payload.append(
            {
                "pid": item.process.pid,
                "user": item.process.user,
                "command": item.process.command,
                "severity": item.severity,
                "risk_score": item.risk_score,
                "account_scope": item.permissions.account_scope if item.permissions else "unknown",
                "privileged_account": item.permissions.privileged_account if item.permissions else False,
                "listening_ports": item.permissions.listening_ports if item.permissions else [],
                "macos_entitlements": item.permissions.macos_entitlements if item.permissions else [],
            }
        )

    if as_json:
        print(json.dumps(payload, indent=2))
        return 0

    if not payload:
        print("No AI agent/model processes with permission signals detected.")
        return 1

    for row in payload:
        print(
            f"PID {row['pid']} [{row['severity'].upper()} {row['risk_score']}] "
            f"user={row['user']} scope={row['account_scope']} ports={','.join(row['listening_ports']) or '-'}"
        )
        print(f"  cmd: {row['command']}")
    return 0


def _protect(allowlist: list[str], min_severity: str, as_json: bool) -> int:
    findings = detect_agents(list_processes(), allowlist_keywords=allowlist)
    rank = {"low": 0, "medium": 1, "high": 2}
    threshold = rank[min_severity]
    selected = [f for f in findings if rank.get(f.severity, 0) >= threshold]

    actions = []
    for item in selected:
        actions.append(
            {
                "pid": item.process.pid,
                "severity": item.severity,
                "risk_score": item.risk_score,
                "command": item.process.command,
                "recommended_actions": [
                    "Verify executable path and signature",
                    "Confirm expected owner/process parent",
                    "Block network egress if untrusted",
                    "Terminate process manually if confirmed malicious",
                ],
            }
        )

    if as_json:
        print(json.dumps(actions, indent=2))
        return 0

    if not actions:
        print(f"No findings at or above severity '{min_severity}'.")
        return 1

    print(f"Protection actions for {len(actions)} finding(s):")
    for action in actions:
        print(
            f"- PID {action['pid']} [{action['severity'].upper()} {action['risk_score']}] {action['command']}"
        )
        print("  actions: " + "; ".join(action["recommended_actions"]))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skopos",
        description="Watcher/Guardian CLI for detecting AI agents and model runtimes.",
    )
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        help="Keyword allowlist for known-safe agent names (repeatable).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Run a one-time local process scan")
    scan.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    scan.add_argument("--detailed", action="store_true", help="Include per-process security detail")

    perms = sub.add_parser("permissions", help="Report permission posture for detected agent/model processes")
    perms.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    protect = sub.add_parser("protect", help="Show concrete protection actions for risky findings")
    protect.add_argument(
        "--min-severity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Only include findings at or above this severity",
    )
    protect.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    watch = sub.add_parser("watch", help="Continuously monitor for AI/agent process changes")
    watch.add_argument("--interval", type=int, default=10, help="Polling interval in seconds")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        return _scan(args.allow, args.json, args.detailed)
    if args.command == "permissions":
        return _permissions(args.allow, args.json)
    if args.command == "protect":
        return _protect(args.allow, args.min_severity, args.json)
    if args.command == "watch":
        return _watch(args.allow, args.interval)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
