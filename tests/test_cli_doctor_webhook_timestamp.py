"""SPEC 192 — doctor --alert-webhook payload timestamp."""

from __future__ import annotations

import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import atlas_core.cli as _cli
from atlas_core.cli import main

ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_cli, "_has_quality_warning", lambda _r: True)


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


def test_192_timestamp_alani(monkeypatch, tmp_path: Path):
    _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        rc = main(["doctor", "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    assert rc == 0
    body = json.loads(cap[0])
    assert "timestamp" in body
    assert ISO.match(body["timestamp"])


def test_192_alan_sayisi_5(monkeypatch, tmp_path: Path):
    _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        main(["doctor", "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    body = json.loads(cap[0])
    # SPEC 168 4 + SPEC 192 1 = 5
    assert set(body.keys()) == {
        "alert", "warnings", "quality_warnings", "strict", "timestamp",
    }


def test_192_strict_ile_ortogonal(monkeypatch, tmp_path: Path):
    _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        rc = main(["doctor", "--strict",
                   "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    assert rc == 9  # strict + warning
    body = json.loads(cap[0])
    assert body["strict"] is True
    assert "timestamp" in body
