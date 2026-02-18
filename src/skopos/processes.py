from __future__ import annotations

import os
import platform
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .models import PermissionSignals, ProcessInfo


def _run(cmd: list[str]) -> str:
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except (FileNotFoundError, PermissionError, OSError):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def _resolve_executable(command: str) -> Optional[str]:
    if not command:
        return None

    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    if not tokens:
        return None

    head = tokens[0]
    if os.path.isabs(head) and os.path.exists(head):
        return str(Path(head).resolve())

    resolved = shutil.which(head)
    if resolved:
        return str(Path(resolved).resolve())
    return None


def list_processes() -> list[ProcessInfo]:
    system = platform.system().lower()
    if system in {"darwin", "linux"}:
        return _list_processes_unix()
    if system == "windows":
        return _list_processes_windows()
    raise RuntimeError(f"Unsupported platform: {platform.system()}")


def _list_processes_unix() -> list[ProcessInfo]:
    output = _run(["ps", "-axo", "pid=,ppid=,user=,%cpu=,%mem=,command="])
    processes: list[ProcessInfo] = []

    for line in output.splitlines():
        parts = line.strip().split(maxsplit=5)
        if len(parts) < 6:
            continue

        pid_raw, ppid_raw, user, cpu_raw, mem_raw, command = parts
        if not pid_raw.isdigit() or not ppid_raw.isdigit():
            continue

        executable = _resolve_executable(command)
        processes.append(
            ProcessInfo(
                pid=int(pid_raw),
                ppid=int(ppid_raw),
                user=user,
                cpu_percent=_parse_float(cpu_raw),
                mem_percent=_parse_float(mem_raw),
                command=command,
                executable=executable,
            )
        )

    return processes


def _list_processes_windows() -> list[ProcessInfo]:
    output = _run(
        [
            "wmic",
            "process",
            "get",
            "ProcessId,ParentProcessId,Name,CommandLine",
            "/FORMAT:CSV",
        ]
    )
    processes: list[ProcessInfo] = []

    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Node,"):
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue

        command = parts[2] or parts[1]
        pid_raw = parts[-1]
        ppid_raw = parts[-2]
        if not pid_raw.isdigit() or not ppid_raw.isdigit():
            continue

        executable = _resolve_executable(command)
        processes.append(
            ProcessInfo(
                pid=int(pid_raw),
                ppid=int(ppid_raw),
                user="UNKNOWN",
                cpu_percent=0.0,
                mem_percent=0.0,
                command=command,
                executable=executable,
            )
        )

    return processes


def _macos_entitlements(executable: Optional[str]) -> list[str]:
    if platform.system().lower() != "darwin":
        return []
    if not executable or not shutil.which("codesign"):
        return []

    try:
        completed = subprocess.run(
            ["codesign", "-d", "--entitlements", ":-", executable],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, PermissionError, OSError):
        return []
    blob = (completed.stdout or "") + "\n" + (completed.stderr or "")
    return sorted(set(re.findall(r"<key>([^<]+)</key>", blob)))


def _listening_ports(pid: int) -> list[str]:
    if not shutil.which("lsof"):
        return []

    try:
        completed = subprocess.run(
            ["lsof", "-Pan", "-p", str(pid), "-i"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, PermissionError, OSError):
        return []
    if completed.returncode != 0:
        return []

    ports: set[str] = set()
    for line in completed.stdout.splitlines():
        if "LISTEN" not in line:
            continue
        match = re.search(r":(\d+)\s*\(LISTEN\)", line)
        if match:
            ports.add(match.group(1))

    return sorted(ports)


def permission_signals(proc: ProcessInfo) -> PermissionSignals:
    user_lower = proc.user.lower()
    privileged_account = user_lower in {"root", "system", "administrator"}
    scope = "system" if privileged_account else "user"

    ports = _listening_ports(proc.pid)
    entitlements = _macos_entitlements(proc.executable)

    return PermissionSignals(
        privileged_account=privileged_account,
        account_scope=scope,
        has_listening_socket=bool(ports),
        listening_ports=ports,
        macos_entitlements=entitlements,
    )
