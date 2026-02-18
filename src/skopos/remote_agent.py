"""Remote agent client for distributed monitoring."""

from __future__ import annotations

import json
import platform
import socket
import time
from datetime import datetime
from typing import Any, Optional

from .detection import detect_agents
from .processes import list_processes


class RemoteAgent:
    """Remote agent that reports to a central skopos server."""

    def __init__(
        self,
        server_host: str,
        server_port: int,
        agent_name: Optional[str] = None,
        scan_interval: int = 10,
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.agent_name = agent_name or socket.gethostname()
        self.scan_interval = scan_interval
        self.running = False

    def start(self) -> None:
        """Start the remote agent."""
        self.running = True
        print(f"🛡️  Remote agent '{self.agent_name}' starting...")
        print(f"   Server: {self.server_host}:{self.server_port}")
        print(f"   Scan interval: {self.scan_interval}s")
        print()

        while self.running:
            try:
                # Perform scan
                processes = list_processes()
                findings = detect_agents(processes)

                # Prepare report
                report = {
                    "agent_name": self.agent_name,
                    "hostname": socket.gethostname(),
                    "platform": platform.system(),
                    "timestamp": datetime.now().isoformat(),
                    "findings": [f.to_dict() for f in findings],
                    "stats": {
                        "total": len(findings),
                        "high": sum(1 for f in findings if f.severity == "high"),
                        "medium": sum(1 for f in findings if f.severity == "medium"),
                        "low": sum(1 for f in findings if f.severity == "low"),
                    },
                }

                # Send to server
                self._send_report(report)

            except Exception as e:
                print(f"Error in scan cycle: {e}")

            time.sleep(self.scan_interval)

    def stop(self) -> None:
        """Stop the remote agent."""
        self.running = False
        print(f"\n✅ Remote agent '{self.agent_name}' stopped")

    def _send_report(self, report: dict[str, Any]) -> None:
        """Send report to central server via HTTP."""
        try:
            import http.client

            conn = http.client.HTTPConnection(self.server_host, self.server_port)
            headers = {"Content-Type": "application/json"}
            body = json.dumps(report)

            conn.request("POST", "/api/remote/report", body, headers)
            response = conn.getresponse()

            if response.status == 200:
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Report sent: {report['stats']['total']} findings"
                )
            else:
                print(f"Server returned status {response.status}")

            conn.close()

        except ConnectionRefusedError:
            print(f"Cannot connect to server at {self.server_host}:{self.server_port}")
        except Exception as e:
            print(f"Error sending report: {e}")


# Storage for remote agent reports
_remote_reports: dict[str, dict[str, Any]] = {}


def get_remote_reports() -> dict[str, dict[str, Any]]:
    """Get all remote agent reports."""
    return _remote_reports.copy()


def register_remote_report(agent_name: str, report: dict[str, Any]) -> None:
    """Register a report from a remote agent."""
    _remote_reports[agent_name] = {
        **report,
        "last_seen": datetime.now().isoformat(),
    }
