"""Scheduled scan management for skopos."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .detection import detect_agents
from .processes import list_processes


class ScheduledScan:
    """A scheduled scan configuration."""

    def __init__(
        self,
        name: str,
        interval: int,
        enabled: bool = True,
        allowlist: Optional[list[str]] = None,
        min_severity: str = "low",
        callback: Optional[Callable[[list[Any]], None]] = None,
    ):
        self.name = name
        self.interval = interval  # seconds
        self.enabled = enabled
        self.allowlist = allowlist or []
        self.min_severity = min_severity
        self.callback = callback
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "interval": self.interval,
            "enabled": self.enabled,
            "allowlist": self.allowlist,
            "min_severity": self.min_severity,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
        }


class Scheduler:
    """Manages scheduled scans."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".config" / "skopos"
        self.config_file = self.config_dir / "schedules.json"
        self.schedules: dict[str, ScheduledScan] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._load()

    def _load(self) -> None:
        """Load schedules from config file."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    schedule = ScheduledScan(
                        name=item["name"],
                        interval=item["interval"],
                        enabled=item.get("enabled", True),
                        allowlist=item.get("allowlist", []),
                        min_severity=item.get("min_severity", "low"),
                    )
                    self.schedules[schedule.name] = schedule
        except Exception as e:
            print(f"Error loading schedules: {e}")

    def save(self) -> None:
        """Save schedules to config file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        data = [s.to_dict() for s in self.schedules.values()]
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add(self, schedule: ScheduledScan) -> None:
        """Add or update a scheduled scan."""
        self.schedules[schedule.name] = schedule
        self.save()

    def remove(self, name: str) -> bool:
        """Remove a scheduled scan."""
        if name in self.schedules:
            del self.schedules[name]
            self.save()
            return True
        return False

    def get(self, name: str) -> Optional[ScheduledScan]:
        """Get a scheduled scan by name."""
        return self.schedules.get(name)

    def list(self) -> list[ScheduledScan]:
        """List all scheduled scans."""
        return list(self.schedules.values())

    def start(self) -> None:
        """Start the scheduler thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the scheduler thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _run(self) -> None:
        """Main scheduler loop."""
        while self.running:
            now = datetime.now()

            for schedule in self.schedules.values():
                if not schedule.enabled:
                    continue

                # Check if it's time to run
                should_run = False
                if schedule.last_run is None:
                    should_run = True
                else:
                    elapsed = (now - schedule.last_run).total_seconds()
                    if elapsed >= schedule.interval:
                        should_run = True

                if should_run:
                    self._execute_scan(schedule)
                    schedule.last_run = now

            time.sleep(1)  # Check every second

    def _execute_scan(self, schedule: ScheduledScan) -> None:
        """Execute a scheduled scan."""
        try:
            processes = list_processes()
            findings = detect_agents(processes, allowlist_keywords=schedule.allowlist)

            # Filter by severity
            severity_order = {"low": 0, "medium": 1, "high": 2}
            min_level = severity_order.get(schedule.min_severity, 0)
            filtered = [
                f for f in findings if severity_order.get(f.severity, 0) >= min_level
            ]

            # Call callback if provided
            if schedule.callback:
                schedule.callback(filtered)

        except Exception as e:
            print(f"Error executing scheduled scan '{schedule.name}': {e}")
