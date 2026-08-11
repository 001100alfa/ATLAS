"""SPEC 186 — vault verify --alert-webhook payload timestamp alanı."""

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
    vault = tmp_path / "v"
    vault.mkdir()
    (vault / "note.md").write_text("[[missing]]", encoding="utf-8")
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(vault))
    return vault


def _serve(capture: list):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            n = int(self.headers.get("Content-Length", "0"))
            capture.append(self.rfile.read(n).decode())
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_a, **_kw):  # noqa: A003
            return

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)

    def _s():
        srv.shutdown()
        srv.server_close()
        t.join(timeout=2.0)
    return port, _s


def test_186_timestamp_alani(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        rc = main(["vault", "verify",
                   "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    assert rc == 0
    body = json.loads(cap[0])
    assert "timestamp" in body
    assert ISO_RE.match(body["timestamp"])


def test_186_mevcut_alanlar_dokunulmadi(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    cap: list = []
    port, sd = _serve(cap)
    try:
        main(["vault", "verify",
              "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    body = json.loads(cap[0])
    # SPEC 165 mevcut 8 + SPEC 186 1 = 9
    assert set(body.keys()) == {
        "alert", "vault_root", "notes_total", "links_total",
        "tags_total", "broken_links", "orphan_notes", "orphan_tags",
        "timestamp",
    }
