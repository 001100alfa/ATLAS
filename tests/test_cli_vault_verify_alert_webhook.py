"""SPEC 165 — atlas vault verify --alert-webhook URL testleri."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return tmp_path / "v"


def _seed_vault(vault_root: Path, *, dirty: bool) -> None:
    """Vault dizini oluştur; dirty=True → kırık wikilink içerir."""
    vault_root.mkdir(parents=True, exist_ok=True)
    if dirty:
        (vault_root / "note.md").write_text(
            "# note\n\nSee [[missing-target]] for more.\n",
            encoding="utf-8",
        )
    else:
        # temiz vault: iki not, birbirine wikilink → hiç orphan yok
        (vault_root / "a.md").write_text(
            "# a\n\nLink to [[b]].\n", encoding="utf-8",
        )
        (vault_root / "b.md").write_text(
            "# b\n\nLink to [[a]].\n", encoding="utf-8",
        )


def _serve(status: int = 200, capture: list | None = None):
    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            if capture is not None:
                capture.append({
                    "path": self.path,
                    "body": body.decode("utf-8"),
                    "content_type": self.headers.get("Content-Type"),
                    "user_agent": self.headers.get("User-Agent"),
                })
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


def test_165_bulgu_varsa_post_atilir(monkeypatch, tmp_path, capsys):
    """Kırık link varsa POST atılır (200 yanıt)."""
    vault = _env(monkeypatch, tmp_path)
    _seed_vault(vault, dirty=True)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "verify",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["alert"] == "vault-verify"
    assert body["broken_links"] >= 1
    assert "vault_root" in body
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarılı" in err


def test_165_temiz_vault_post_atilmaz(monkeypatch, tmp_path, capsys):
    """is_clean True → POST atılmaz (sessiz)."""
    vault = _env(monkeypatch, tmp_path)
    _seed_vault(vault, dirty=False)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "verify",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert capture == []
    err = capsys.readouterr().err
    assert "alert-webhook" not in err


def test_165_post_bassrisiz_exit_code_korur(monkeypatch, tmp_path, capsys):
    """POST 500 → başarısız stderr; exit code KORUR (SPEC 064 kalıbı)."""
    vault = _env(monkeypatch, tmp_path)
    _seed_vault(vault, dirty=True)
    port, shutdown = _serve(status=500)
    try:
        rc = main([
            "vault", "verify",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0  # exit code KORUR
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarısız" in err
    assert "HTTP 500" in err


def test_165_strict_ile_ortogonal(monkeypatch, tmp_path, capsys):
    """--strict ile birlikte: POST atılır + exit 4 (--strict)."""
    vault = _env(monkeypatch, tmp_path)
    _seed_vault(vault, dirty=True)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "vault", "verify", "--strict",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 4
    assert len(capture) == 1


def test_165_ge_hersey_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--alert-webhook YOK → SPEC 042 davranışı AYNI."""
    vault = _env(monkeypatch, tmp_path)
    _seed_vault(vault, dirty=True)
    rc = main(["vault", "verify"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "vault verify" in out
    assert "kırık link" in out


def test_165_url_scheme_gecersiz(monkeypatch, tmp_path, capsys):
    """SSRF savunma: file:// scheme → POST başarısız."""
    vault = _env(monkeypatch, tmp_path)
    _seed_vault(vault, dirty=True)
    rc = main([
        "vault", "verify",
        "--alert-webhook", "file:///etc/passwd",
    ])
    assert rc == 0  # exit code KORUR
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarısız" in err
