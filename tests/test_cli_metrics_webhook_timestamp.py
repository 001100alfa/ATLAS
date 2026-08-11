"""SPEC 187 — metrics --alert-webhook payload timestamp."""

from __future__ import annotations

import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    m = tmp_path / "metrics.jsonl"
    m.write_text(json.dumps({
        "ts": "2026-08-10T12:00:00",
        "in": 100, "out": 5, "cache_c": 0, "cache_r": 5, "cost": 0.01,
    }) + "\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_METRICS", str(m))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return m


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


def test_187_timestamp_alani(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        rc = main(["metrics", "--limit", "10", "--alert", "50",
                   "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    assert rc == 8
    body = json.loads(cap[0])
    assert "timestamp" in body
    assert ISO_RE.match(body["timestamp"])


def test_187_mevcut_alanlar_dokunulmadi(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        main(["metrics", "--limit", "10", "--alert", "50",
              "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    body = json.loads(cap[0])
    for k in ("alert", "hit_ratio_pct", "threshold_pct", "records",
              "tokens_in", "tokens_out", "cache_creation", "cache_read",
              "message", "timestamp"):
        assert k in body


def test_187_alert_window_ile_ortogonal(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        main(["metrics", "--limit", "10", "--alert", "50",
              "--alert-window", "60",
              "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    body = json.loads(cap[0])
    assert "timestamp" in body
    assert body["alert_window_minutes"] == 60
