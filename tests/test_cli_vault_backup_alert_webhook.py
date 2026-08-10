"""SPEC 178 — atlas vault backup --alert-webhook URL testleri."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    vault = tmp_path / "v"
    vault.mkdir()
    (vault / "note.md").write_text("# hi\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(vault))
    monkeypatch.chdir(tmp_path)
    return vault


def _serve(status: int = 200, capture: list | None = None):
    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            if capture is not None:
                capture.append({"body": body.decode("utf-8")})
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_a, **_kw):  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)

    def _shutdown():
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
    return port, _shutdown


def test_178_basarili_backup_post_atilmaz(monkeypatch, tmp_path, capsys):
    """Başarılı backup (exit 0) → POST atılmaz (sessiz)."""
    _env(monkeypatch, tmp_path)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "backup",
            "--archive-root", str(tmp_path / "arc"),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert capture == []


def test_178_backup_error_post_atilir(monkeypatch, tmp_path, capsys):
    """VaultBackupError (exit 6) → POST atılır."""
    from atlas_core.memory import vault_backup as _vb
    _env(monkeypatch, tmp_path)

    def _raise(*_a, **_kw):
        raise _vb.VaultBackupError("simulated backup fail")

    monkeypatch.setattr(_vb, "backup_vault", _raise)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "backup",
            "--archive-root", str(tmp_path / "arc"),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 6
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["alert"] == "vault-backup"
    assert body["phase"] == "backup"
    assert body["exit_code"] == 6
    assert body["action"] == "backup"
    assert "simulated backup fail" in body["error"]
    assert "vault_root" in body


def test_178_backup_auto_action_alaninda(monkeypatch, tmp_path, capsys):
    """--auto ile birlikte action=backup-auto payload'a yansır."""
    from atlas_core.memory import vault_backup as _vb
    _env(monkeypatch, tmp_path)

    def _raise(*_a, **_kw):
        raise _vb.VaultBackupError("boom")

    monkeypatch.setattr(_vb, "backup_vault", _raise)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "backup", "--auto",
            "--archive-root", str(tmp_path / "arc"),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 6
    body = json.loads(capture[0]["body"])
    assert body["action"] == "backup-auto"


def test_178_prune_error_post_atilir(monkeypatch, tmp_path, capsys):
    """prune_backups VaultBackupError → phase=prune POST."""
    from atlas_core.memory import vault_backup as _vb
    _env(monkeypatch, tmp_path)

    def _raise_prune(*_a, **_kw):
        raise _vb.VaultBackupError("prune fail")

    monkeypatch.setattr(_vb, "prune_backups", _raise_prune)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "backup", "--keep", "3",
            "--archive-root", str(tmp_path / "arc"),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 6
    body = json.loads(capture[0]["body"])
    assert body["phase"] == "prune"


def test_178_spec_hatasi_exit_2_post_atmaz(monkeypatch, tmp_path, capsys):
    """SPEC HATASI (exit 2) POST atmaz — kullanıcı yanlış argüman."""
    _env(monkeypatch, tmp_path)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "backup", "--keep", "0",  # invalid
            "--archive-root", str(tmp_path / "arc"),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 2
    assert capture == []


def test_178_vault_dizini_yok_post_atmaz(monkeypatch, tmp_path, capsys):
    """Vault dizini yok (exit 2 SPEC HATASI) → POST atmaz."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "yok"))
    monkeypatch.chdir(tmp_path)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "backup",
            "--archive-root", str(tmp_path / "arc"),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 2
    assert capture == []


def test_178_post_basarisiz_exit_code_korur(monkeypatch, tmp_path, capsys):
    """POST 500 → başarısız stderr; exit code KORUR."""
    from atlas_core.memory import vault_backup as _vb
    _env(monkeypatch, tmp_path)

    def _raise(*_a, **_kw):
        raise _vb.VaultBackupError("boom")

    monkeypatch.setattr(_vb, "backup_vault", _raise)
    port, shutdown = _serve(status=500)
    try:
        rc = main([
            "vault", "backup",
            "--archive-root", str(tmp_path / "arc"),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 6
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarısız" in err
    assert "HTTP 500" in err


def test_178_schema_modda_webhook_yok(monkeypatch, tmp_path, capsys):
    """SPEC 154 --schema kısa devre --alert-webhook'u YOK sayar."""
    _env(monkeypatch, tmp_path)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "backup", "--schema",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert capture == []


def test_178_webhook_yok_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--alert-webhook YOK → SPEC 041 davranışı AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "backup",
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "vault yedeği yazıldı" in out
