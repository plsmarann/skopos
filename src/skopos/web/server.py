"""Flask web server for skopos dashboard."""

from __future__ import annotations

import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from flask import Flask, jsonify, render_template, request
    from flask_cors import CORS
    from flask_socketio import SocketIO, emit

    HAS_FLASK = True
    HAS_SOCKETIO = True
except ImportError:
    HAS_FLASK = False
    HAS_SOCKETIO = False

from ..detection import detect_agents
from ..processes import list_processes

# Global history storage (in-memory)
_history: list[dict[str, Any]] = []
_max_history = 100


def create_app() -> tuple[Any, Any]:
    """Create Flask application with SocketIO."""
    if not HAS_FLASK:
        raise RuntimeError(
            "Flask not installed. Install with: pip install skopos[web]"
        )

    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"

    app = Flask(
        __name__, template_folder=str(template_dir), static_folder=str(static_dir)
    )
    app.config["SECRET_KEY"] = os.urandom(24).hex()
    CORS(app)

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

    # Store allowlist in app config
    app.config["ALLOWLIST"] = []
    app.config["CLIENTS"] = set()  # Track connected clients

    @app.route("/")
    def index() -> str:
        """Render dashboard."""
        return render_template("dashboard.html")

    @app.route("/api/scan")
    def api_scan() -> Any:
        """Get current detection results."""
        try:
            processes = list_processes()
            allowlist = app.config.get("ALLOWLIST", [])
            findings = detect_agents(processes, allowlist_keywords=allowlist)
            return jsonify(
                {
                    "success": True,
                    "count": len(findings),
                    "findings": [f.to_dict() for f in findings],
                }
            )
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/stats")
    def api_stats() -> Any:
        """Get statistics summary."""
        try:
            processes = list_processes()
            allowlist = app.config.get("ALLOWLIST", [])
            findings = detect_agents(processes, allowlist_keywords=allowlist)

            stats = {
                "total": len(findings),
                "high": sum(1 for f in findings if f.severity == "high"),
                "medium": sum(1 for f in findings if f.severity == "medium"),
                "low": sum(1 for f in findings if f.severity == "low"),
            }

            # Count unique agents
            agents: dict[str, int] = {}
            for f in findings:
                for kw in f.ai_agent_keywords + f.model_keywords:
                    agents[kw] = agents.get(kw, 0) + 1

            return jsonify(
                {
                    "success": True,
                    "stats": stats,
                    "agents": dict(sorted(agents.items(), key=lambda x: -x[1])[:10]),
                }
            )
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kill/<int:pid>", methods=["POST"])
    def api_kill(pid: int) -> Any:
        """Kill a process by PID."""
        try:
            data = request.get_json() or {}
            confirm = data.get("confirm", False)

            if not confirm:
                return jsonify(
                    {"success": False, "error": "Confirmation required"}
                ), 400

            # Safety checks
            if pid < 2:
                return jsonify(
                    {"success": False, "error": "Cannot kill system process (PID < 2)"}
                ), 403

            # Check if process exists and get info
            processes = list_processes()
            target = next((p for p in processes if p.pid == pid), None)

            if not target:
                return jsonify(
                    {"success": False, "error": f"Process {pid} not found"}
                ), 404

            # Prevent killing critical system processes
            critical_names = [
                "systemd",
                "init",
                "launchd",
                "kernel",
                "WindowServer",
            ]
            if any(name in target.command.lower() for name in critical_names):
                return jsonify(
                    {
                        "success": False,
                        "error": f"Refusing to kill critical system process: {target.command[:50]}",
                    }
                ), 403

            # Attempt to kill the process
            try:
                os.kill(pid, signal.SIGTERM)
                return jsonify(
                    {
                        "success": True,
                        "message": f"Sent SIGTERM to PID {pid}",
                        "process": target.command[:100],
                    }
                )
            except ProcessLookupError:
                return jsonify(
                    {"success": False, "error": "Process no longer exists"}
                ), 404
            except PermissionError:
                return jsonify(
                    {
                        "success": False,
                        "error": "Permission denied. May require elevated privileges.",
                    }
                ), 403

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/allowlist", methods=["GET", "POST"])
    def api_allowlist() -> Any:
        """Get or update allowlist."""
        if request.method == "GET":
            return jsonify(
                {"success": True, "allowlist": app.config.get("ALLOWLIST", [])}
            )

        try:
            data = request.get_json() or {}
            keyword = data.get("keyword", "").strip().lower()

            if not keyword:
                return jsonify(
                    {"success": False, "error": "Keyword required"}
                ), 400

            allowlist = app.config.get("ALLOWLIST", [])

            action = data.get("action", "add")
            if action == "add" and keyword not in allowlist:
                allowlist.append(keyword)
                app.config["ALLOWLIST"] = allowlist
                return jsonify(
                    {"success": True, "message": f"Added '{keyword}' to allowlist"}
                )
            elif action == "remove" and keyword in allowlist:
                allowlist.remove(keyword)
                app.config["ALLOWLIST"] = allowlist
                return jsonify(
                    {"success": True, "message": f"Removed '{keyword}' from allowlist"}
                )
            else:
                return jsonify(
                    {"success": False, "error": f"Keyword already in allowlist"}
                ), 400

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/history")
    def api_history() -> Any:
        """Get historical data."""
        try:
            return jsonify({"success": True, "history": _history})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # WebSocket event handlers
    @socketio.on("connect")
    def handle_connect() -> None:
        """Handle client connection."""
        app.config["CLIENTS"].add(request.sid)
        emit("status", {"message": "Connected to skopos server"})

    @socketio.on("disconnect")
    def handle_disconnect() -> None:
        """Handle client disconnection."""
        app.config["CLIENTS"].discard(request.sid)

    @socketio.on("request_scan")
    def handle_request_scan() -> None:
        """Handle manual scan request."""
        try:
            processes = list_processes()
            allowlist = app.config.get("ALLOWLIST", [])
            findings = detect_agents(processes, allowlist_keywords=allowlist)
            emit("scan_result", {"findings": [f.to_dict() for f in findings]})
        except Exception as e:
            emit("error", {"message": str(e)})

    # Background scanner function
    def background_scanner() -> None:
        """Background thread to scan and emit updates via WebSocket."""
        previous_pids: set[int] = set()

        with app.app_context():
            while True:
                try:
                    processes = list_processes()
                    allowlist = app.config.get("ALLOWLIST", [])
                    findings = detect_agents(processes, allowlist_keywords=allowlist)

                    current_pids = {f.process.pid for f in findings}

                    # Detect changes
                    new_pids = current_pids - previous_pids
                    removed_pids = previous_pids - current_pids

                    # Store in history
                    entry = {
                        "timestamp": datetime.now().isoformat(),
                        "total": len(findings),
                        "high": sum(1 for f in findings if f.severity == "high"),
                        "medium": sum(1 for f in findings if f.severity == "medium"),
                        "low": sum(1 for f in findings if f.severity == "low"),
                        "new_pids": list(new_pids),
                        "removed_pids": list(removed_pids),
                    }
                    _history.append(entry)
                    if len(_history) > _max_history:
                        _history.pop(0)

                    # Compute stats
                    stats = {
                        "total": entry["total"],
                        "high": entry["high"],
                        "medium": entry["medium"],
                        "low": entry["low"],
                    }

                    agents: dict[str, int] = {}
                    for f in findings:
                        for kw in f.ai_agent_keywords + f.model_keywords:
                            agents[kw] = agents.get(kw, 0) + 1

                    # Emit to all connected clients
                    if app.config["CLIENTS"]:
                        socketio.emit(
                            "update",
                            {
                                "findings": [f.to_dict() for f in findings],
                                "stats": stats,
                                "agents": dict(
                                    sorted(agents.items(), key=lambda x: -x[1])[:10]
                                ),
                                "changes": {
                                    "new": list(new_pids),
                                    "removed": list(removed_pids),
                                },
                            },
                        )

                        # Alert on high severity
                        high_severity = [f for f in findings if f.severity == "high"]
                        if high_severity and new_pids:
                            for f in high_severity:
                                if f.process.pid in new_pids:
                                    socketio.emit(
                                        "alert",
                                        {
                                            "severity": "high",
                                            "pid": f.process.pid,
                                            "user": f.process.user,
                                            "command": f.process.command,
                                            "risk_score": f.risk_score,
                                            "reasons": f.reasons,
                                        },
                                    )

                    previous_pids = current_pids

                except Exception as e:
                    print(f"Background scanner error: {e}", file=sys.stderr)

                time.sleep(3)  # Scan every 3 seconds

    # Start background scanner
    socketio.start_background_task(background_scanner)

    return app, socketio


def run_server(host: str = "127.0.0.1", port: int = 8080, debug: bool = False) -> None:
    """Run the web server."""
    if not HAS_FLASK:
        print("❌ Flask not installed.", file=sys.stderr)
        print("   Install with: pip install skopos[web]", file=sys.stderr)
        sys.exit(1)

    app, socketio = create_app()

    print(f"🛡️  Starting skopos web dashboard (Phase 2)...")
    print(f"   URL: http://{host}:{port}")
    print(f"   ✨ Features: WebSocket live updates, Charts, Alerts")
    print(f"   Press Ctrl+C to stop")
    print()

    try:
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\n✅ Stopped web server")
