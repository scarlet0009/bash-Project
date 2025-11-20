#!/usr/bin/env python3
"""
SmartLogWatcher Dashboard (Flask)
- Live events (SSE) from suspicious.log
- Block/unblock endpoints that call the bash helper
- Summary endpoints for charts
"""

import os
import csv
import time
import subprocess
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request, send_from_directory, abort
from flask_basicauth import BasicAuth
from dotenv import load_dotenv
from pathlib import Path
from threading import Event, Thread

# Load .env if present
load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "/var/log/smartlogwatcher"))
SUSPICIOUS_LOG = Path(os.getenv("SUSPICIOUS_LOG", DATA_DIR / "suspicious.log"))
BLOCKED_FILE = Path(os.getenv("BLOCKED_FILE", DATA_DIR / "blocked_ips.csv"))
REPORT_DIR = Path(os.getenv("REPORT_DIR", DATA_DIR / "reports"))

BLOCK_HELPER = "/usr/local/bin/smartlogwatcher_block.sh"  # assumes installed
# Basic Auth
BASIC_USERNAME = os.getenv("BASIC_AUTH_USERNAME", "admin")
BASIC_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD", "changeme")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
DEBUG = bool(int(os.getenv("DEBUG", 0)))

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['BASIC_AUTH_USERNAME'] = BASIC_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = BASIC_PASSWORD
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)

# Utility: read blocked CSV
def read_blocked():
    entries = []
    if not BLOCKED_FILE.exists():
        return entries
    try:
        with BLOCKED_FILE.open() as fh:
            reader = csv.reader(fh)
            for row in reader:
                if not row:
                    continue
                ip = row[0].strip()
                blocked_at = int(row[1]) if len(row) > 1 and row[1].isdigit() else None
                unblock_at = int(row[2]) if len(row) > 2 and row[2].isdigit() else None
                reason = row[3] if len(row) > 3 else ""
                entries.append({
                    "ip": ip, "blocked_at": blocked_at, "unblock_at": unblock_at, "reason": reason
                })
    except Exception:
        pass
    return entries

# Utility: parse suspicious.log tail for last N lines
def tail_file(file_path: Path, lines:int=200):
    if not file_path.exists():
        return []
    # naive but reliable read
    with file_path.open(errors='ignore') as fh:
        all_lines = fh.readlines()
    return [l.rstrip('\n') for l in all_lines[-lines:]]

# Endpoint: Dashboard homepage
@app.route("/")
@basic_auth.required
def index():
    blocked = read_blocked()
    recent = tail_file(SUSPICIOUS_LOG, lines=200)
    return render_template("index.html", blocked=blocked, recent=recent)

# SSE: stream new lines from suspicious.log
@app.route("/stream")
@basic_auth.required
def stream():
    def generator(stop_event: Event):
        # start from end of file
        if not SUSPICIOUS_LOG.exists():
            SUSPICIOUS_LOG.parent.mkdir(parents=True, exist_ok=True)
            SUSPICIOUS_LOG.write_text("")
        with SUSPICIOUS_LOG.open('r', errors='ignore') as fh:
            # go to EOF
            fh.seek(0, os.SEEK_END)
            while not stop_event.is_set():
                line = fh.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                # SSE format
                yield f"data: {line.rstrip()}\n\n"
    stop_event = Event()
    return Response(generator(stop_event), mimetype="text/event-stream")

# API: get blocked list JSON
@app.route("/api/blocked")
@basic_auth.required
def api_blocked():
    return jsonify(read_blocked())

# API: unblock IP (calls helper)
@app.route("/api/unblock", methods=["POST"])
@basic_auth.required
def api_unblock():
    data = request.get_json() or {}
    ip = data.get("ip")
    if not ip:
        return jsonify({"error": "ip required"}), 400
    try:
        # call helper script (unblock)
        subprocess.check_call([BLOCK_HELPER, "unblock", ip])
        return jsonify({"ok": True, "ip": ip})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "failed to unblock", "detail": str(e)}), 500

# API: manual block (duration optional)
@app.route("/api/block", methods=["POST"])
@basic_auth.required
def api_block():
    data = request.get_json() or {}
    ip = data.get("ip")
    duration = str(int(data.get("duration", 86400)))  # seconds
    reason = data.get("reason", "manual")
    if not ip:
        return jsonify({"error": "ip required"}), 400
    try:
        subprocess.check_call([BLOCK_HELPER, "block", ip, duration, reason])
        return jsonify({"ok": True, "ip": ip})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "failed to block", "detail": str(e)}), 500

# API: top offenders (read ip_attempts files)
@app.route("/api/top_offenders")
@basic_auth.required
def api_top_offenders():
    ipdir = DATA_DIR / "ip_attempts"
    results = []
    if ipdir.exists() and ipdir.is_dir():
        for f in ipdir.glob("*.timestamps"):
            ip = f.stem
            try:
                cnt = sum(1 for _ in f.open())
            except Exception:
                cnt = 0
            results.append({"ip": ip, "count": cnt})
    results.sort(key=lambda r: r["count"], reverse=True)
    return jsonify(results[:30])

# API: trigger report creation (calls existing report script)
@app.route("/api/generate_report", methods=["POST"])
@basic_auth.required
def api_generate_report():
    REPORT_SCRIPT = "/usr/local/bin/smartlogwatcher_report.sh"
    if not Path(REPORT_SCRIPT).exists():
        return jsonify({"error": "report script missing"}), 500
    try:
        subprocess.check_call([REPORT_SCRIPT])
        latest = sorted(REPORT_DIR.glob("report-*.txt"))[-1] if list(REPORT_DIR.glob("report-*.txt")) else None
        return jsonify({"ok": True, "report": str(latest) if latest else None})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "report generation failed", "detail": str(e)}), 500

# API: download report file
@app.route("/reports/<path:filename>")
@basic_auth.required
def download_report(filename):
    if not REPORT_DIR.exists():
        abort(404)
    return send_from_directory(str(REPORT_DIR), filename, as_attachment=True)

# Basic health
@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": int(time.time())})

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
