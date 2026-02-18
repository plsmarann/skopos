"""Process control operations for skopos."""

from __future__ import annotations

import os
import platform
import signal
import subprocess
from typing import Optional


class ProcessControl:
    """Advanced process control operations."""

    @staticmethod
    def pause(pid: int) -> tuple[bool, str]:
        """Pause (suspend) a process.

        Returns:
            (success: bool, message: str)
        """
        try:
            if platform.system() == "Windows":
                # Windows: Use pssuspend or PowerShell
                completed = subprocess.run(
                    ["powershell", "-Command", f"Suspend-Process -Id {pid}"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode == 0:
                    return True, f"Process {pid} paused"
                return False, f"Failed to pause process: {completed.stderr}"
            else:
                # Unix: Send SIGSTOP
                os.kill(pid, signal.SIGSTOP)
                return True, f"Process {pid} paused (SIGSTOP)"
        except ProcessLookupError:
            return False, f"Process {pid} not found"
        except PermissionError:
            return False, f"Permission denied to pause process {pid}"
        except Exception as e:
            return False, f"Error pausing process: {str(e)}"

    @staticmethod
    def resume(pid: int) -> tuple[bool, str]:
        """Resume (continue) a paused process.

        Returns:
            (success: bool, message: str)
        """
        try:
            if platform.system() == "Windows":
                # Windows: Use psresume or PowerShell
                completed = subprocess.run(
                    ["powershell", "-Command", f"Resume-Process -Id {pid}"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode == 0:
                    return True, f"Process {pid} resumed"
                return False, f"Failed to resume process: {completed.stderr}"
            else:
                # Unix: Send SIGCONT
                os.kill(pid, signal.SIGCONT)
                return True, f"Process {pid} resumed (SIGCONT)"
        except ProcessLookupError:
            return False, f"Process {pid} not found"
        except PermissionError:
            return False, f"Permission denied to resume process {pid}"
        except Exception as e:
            return False, f"Error resuming process: {str(e)}"

    @staticmethod
    def kill(pid: int, force: bool = False) -> tuple[bool, str]:
        """Kill a process gracefully or forcefully.

        Args:
            pid: Process ID
            force: If True, use SIGKILL (Unix) or /F (Windows)

        Returns:
            (success: bool, message: str)
        """
        try:
            if platform.system() == "Windows":
                # Windows: Use taskkill
                flag = "/F" if force else "/T"
                completed = subprocess.run(
                    ["taskkill", flag, "/PID", str(pid)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode == 0:
                    return True, f"Process {pid} killed"
                return False, f"Failed to kill process: {completed.stderr}"
            else:
                # Unix: Send SIGKILL or SIGTERM
                sig = signal.SIGKILL if force else signal.SIGTERM
                os.kill(pid, sig)
                sig_name = "SIGKILL" if force else "SIGTERM"
                return True, f"Process {pid} killed ({sig_name})"
        except ProcessLookupError:
            return False, f"Process {pid} not found"
        except PermissionError:
            return False, f"Permission denied to kill process {pid}"
        except Exception as e:
            return False, f"Error killing process: {str(e)}"

    @staticmethod
    def get_status(pid: int) -> Optional[str]:
        """Get process status (running, sleeping, stopped, etc.).

        Returns:
            Status string or None if process not found
        """
        try:
            if platform.system() == "Windows":
                completed = subprocess.run(
                    ["powershell", "-Command", f"(Get-Process -Id {pid}).Responding"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode == 0:
                    responding = completed.stdout.strip().lower() == "true"
                    return "running" if responding else "not responding"
                return None
            else:
                # Unix: Check /proc or use ps
                completed = subprocess.run(
                    ["ps", "-o", "state=", "-p", str(pid)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode == 0:
                    state = completed.stdout.strip()
                    status_map = {
                        "R": "running",
                        "S": "sleeping",
                        "D": "disk sleep",
                        "T": "stopped",
                        "t": "tracing stop",
                        "Z": "zombie",
                        "X": "dead",
                    }
                    return status_map.get(state[0], state)
                return None
        except Exception:
            return None
