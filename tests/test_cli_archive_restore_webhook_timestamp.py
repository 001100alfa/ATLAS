"""SPEC 198 — archive --restore --alert-webhook payload timestamp."""

from __future__ import annotations

import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main

ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    tasks = tmp_path / "tasks"
    arc = tmp_path / "arc"
    tasks.mkdir()
    arc.mkdir()
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.chdir(tmp_path)
    return tasks, arc


def _serve(cap: list):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            n = int(self.headers.get("Content-Length", "0"))
            cap.append(self.rfile.read(n).decode())
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_a, **_kw):  # noqa: A003
            return

    s = ThreadingHTTPServer(("127.0.0.1", 0), H)
    p = s.server_address[1]
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)

    def _stop():
        s.shutdown()
        s.server_close()
        t.join(timeout=2.0)
    return p, _stop


def test_198_timestamp_alani(monkeypatch, tmp_path):
    tasks, arc = _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        rc = main(["archive", "--restore", "yok", "--apply",
                   "--tasks-root", str(tasks), "--archive-root", str(arc),
                   "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    assert rc == 6
    body = json.loads(cap[0])
    assert "timestamp" in body
    assert ISO.match(body["timestamp"])


def test_198_alan_sayisi_7(monkeypatch, tmp_path):
    tasks, arc = _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        main(["archive", "--restore", "yok", "--apply",
              "--tasks-root", str(tasks), "--archive-root", str(arc),
              "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    body = json.loads(cap[0])
    # SPEC 176 6 + SPEC 198 1 = 7
    assert set(body.keys()) == {
        "alert", "task_id", "search_pattern", "archive_root",
        "error", "exit_code", "timestamp",
    }


def test_198_archive_schema_alert_payload_timestamp(monkeypatch, tmp_path, capsys):
    """SPEC 189 alert_payload'a timestamp eklendi (7 alan)."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["archive", "--schema"])
    assert rc == 0
    d = json.loads(capsys.readouterr().out.strip())
    names = {f["name"] for f in d["alert_payload"]}
    assert "timestamp" in names
    by = {f["name"]: f for f in d["alert_payload"]}
    assert by["timestamp"]["spec"] == "198"


def test_198_restore_schema_alert_payload_fields_timestamp(monkeypatch, tmp_path, capsys):
    """SPEC 182 alert_payload_fields'e timestamp eklendi (7 alan)."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["archive", "--restore", "yok", "--schema",
               "--tasks-root", str(tmp_path / "t"),
               "--archive-root", str(tmp_path / "a")])
    assert rc == 0
    d = json.loads(capsys.readouterr().out.strip())
    names = {f["name"] for f in d["alert_payload_fields"]}
    assert "timestamp" in names
