"""SPEC 168 — atlas doctor --alert-webhook URL testleri."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Sağlıklı temel env; ek test dirty/clean yapılandırmalarını üstüne koyar."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "metrics.jsonl"))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _seed_dirty_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """quality.decisions uyarısı için: DECISIONS.md yok → uyarı."""
    # Boş bir dizinde çalışırız; DECISIONS.md yok → drift + fresh uyarı.
    # ATLAS_MIN_DECISIONS_ENTRIES gibi env'ler tetikleyebilir.
    (tmp_path / "src").mkdir(exist_ok=True)


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


def _force_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_has_quality_warning` monkeypatch → True (deterministik).

    Test'in ortama bağımsız çalışmasını sağlar; SPEC 168 POST akışını
    izole olarak doğrular.
    """
    import atlas_core.cli as _cli
    monkeypatch.setattr(_cli, "_has_quality_warning", lambda _r: True)


def test_168_bulgu_varsa_post_atilir(monkeypatch, tmp_path, capsys):
    """quality warning True → POST atılır (deterministik)."""
    _env(monkeypatch, tmp_path)
    _seed_dirty_env(monkeypatch, tmp_path)
    _force_warning(monkeypatch)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "doctor",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0  # strict yok → exit 0 (webhook exit'i etkilemez)
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["alert"] == "doctor"
    assert "warnings" in body
    assert "quality_warnings" in body
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarılı" in err


def test_168_temiz_ortam_post_atilmaz(monkeypatch, tmp_path, capsys):
    """quality warning False → POST atılmaz (sessiz)."""
    import atlas_core.cli as _cli
    _env(monkeypatch, tmp_path)
    _seed_dirty_env(monkeypatch, tmp_path)
    monkeypatch.setattr(_cli, "_has_quality_warning", lambda _r: False)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "doctor",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert capture == []
    err = capsys.readouterr().err
    assert "[alert-webhook]" not in err


def test_168_post_basarisiz_exit_code_korur(monkeypatch, tmp_path, capsys):
    """POST 500 → başarısız stderr; exit code KORUR."""
    _env(monkeypatch, tmp_path)
    _seed_dirty_env(monkeypatch, tmp_path)
    _force_warning(monkeypatch)
    port, shutdown = _serve(status=500)
    try:
        rc = main([
            "doctor",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0  # exit code KORUR
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarısız" in err
    assert "HTTP 500" in err


def test_168_strict_ile_ortogonal(monkeypatch, tmp_path, capsys):
    """--strict ile birlikte: POST atılır + exit 9 (strict)."""
    _env(monkeypatch, tmp_path)
    _seed_dirty_env(monkeypatch, tmp_path)
    _force_warning(monkeypatch)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "doctor", "--strict",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 9  # strict + warning → exit 9
    assert len(capture) == 1  # webhook YİNE POST atıldı


def test_168_url_scheme_gecersiz(monkeypatch, tmp_path, capsys):
    """SSRF savunma: file:// scheme → POST başarısız (exit code korur)."""
    _env(monkeypatch, tmp_path)
    _seed_dirty_env(monkeypatch, tmp_path)
    _force_warning(monkeypatch)
    rc = main([
        "doctor",
        "--alert-webhook", "file:///etc/passwd",
    ])
    assert rc == 0
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarısız" in err


def test_168_ge_hersey_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--alert-webhook YOK → SPEC 021 doctor davranışı AYNI."""
    _env(monkeypatch, tmp_path)
    _seed_dirty_env(monkeypatch, tmp_path)
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    # Doctor insan çıktısı satırı
    assert "ATLAS doctor" in out or "doctor" in out.lower()


def test_168_parser_alert_webhook_var(monkeypatch, tmp_path, capsys):
    """Parser --alert-webhook argümanını kabul eder (help satırı)."""
    _env(monkeypatch, tmp_path)
    # argparse --help exit 0, çıktıda argüman görünmeli
    with pytest.raises(SystemExit) as exc:
        main(["doctor", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--alert-webhook" in out
