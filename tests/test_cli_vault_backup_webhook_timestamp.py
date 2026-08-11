"""SPEC 199 — vault backup --alert-webhook payload timestamp."""

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
    vault = tmp_path / "v"
    vault.mkdir()
    (vault / "n.md").write_text("# n\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(vault))
    monkeypatch.chdir(tmp_path)
    return vault


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


def test_199_timestamp_alani(monkeypatch, tmp_path):
    from atlas_core.memory import vault_backup as _vb
    _env(monkeypatch, tmp_path)
    monkeypatch.setattr(_vb, "backup_vault",
                        lambda *_a, **_kw: (_ for _ in ()).throw(
                            _vb.VaultBackupError("boom")))
    cap: list = []
    port, sd = _serve(cap)
    try:
        rc = main(["vault", "backup",
                   "--archive-root", str(tmp_path / "arc"),
                   "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    assert rc == 6
    body = json.loads(cap[0])
    assert "timestamp" in body
    assert ISO.match(body["timestamp"])


def test_199_alan_sayisi_7(monkeypatch, tmp_path):
    from atlas_core.memory import vault_backup as _vb
    _env(monkeypatch, tmp_path)
    monkeypatch.setattr(_vb, "backup_vault",
                        lambda *_a, **_kw: (_ for _ in ()).throw(
                            _vb.VaultBackupError("boom")))
    cap: list = []
    port, sd = _serve(cap)
    try:
        main(["vault", "backup",
              "--archive-root", str(tmp_path / "arc"),
              "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    body = json.loads(cap[0])
    # SPEC 178 6 + SPEC 199 1 = 7
    assert set(body.keys()) == {
        "alert", "vault_root", "action", "phase",
        "error", "exit_code", "timestamp",
    }


def test_199_schema_alert_payload_timestamp(monkeypatch, tmp_path, capsys):
    """SPEC 190 alert_payload'a timestamp eklendi."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["vault", "backup", "--schema", "--vault-root", "yok"])
    assert rc == 0
    d = json.loads(capsys.readouterr().out.strip())
    names = {f["name"] for f in d["alert_payload"]}
    assert "timestamp" in names
    by = {f["name"]: f for f in d["alert_payload"]}
    assert by["timestamp"]["spec"] == "199"
