"""Flask web server for skopos dashboard."""

from __future__ import annotations

import os
import signal
import sys
from pathlib import Path
from typing import Any

try:
    from flask import Flask, jsonify, render_template, request
    from flask_cors import CORS

    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from ..detection import detect_agents
from ..processes import list_processes


def create_app() -> Any:
    """Create Flask application."""
    if not HAS_FLASK:
        raise RuntimeError(
            "Flask not installed. Install with: pip install skopos[web]"
        )

    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"

    app = Flask(
        __name__, template_folder=str(template_dir), static_folder=str(static_dir)
    )
    CORS(app)

    # Store allowlist in app config
    app.config["ALLOWLIST"] = []

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

    return app


def run_server(host: str = "127.0.0.1", port: int = 8080, debug: bool = False) -> None:
    """Run the web server."""
    if not HAS_FLASK:
        print("❌ Flask not installed.", file=sys.stderr)
        print("   Install with: pip install skopos[web]", file=sys.stderr)
        sys.exit(1)

    app = create_app()
    print(f"🛡️  Starting skopos web dashboard...")
    print(f"   URL: http://{host}:{port}")
    print(f"   Press Ctrl+C to stop")
    print()

    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\n✅ Stopped web server")
