"""SPEC 177 — doctor --alert-webhook payload strict alanı testleri."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "metrics.jsonl"))
    monkeypatch.chdir(tmp_path)


def _force_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    import atlas_core.cli as _cli
    monkeypatch.setattr(_cli, "_has_quality_warning", lambda _r: True)


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


def test_177_strict_false_payload(monkeypatch, tmp_path, capsys):
    """--strict verilmezse payload.strict = False."""
    _env(monkeypatch, tmp_path)
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
    assert rc == 0
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["alert"] == "doctor"
    assert body["strict"] is False


def test_177_strict_true_payload(monkeypatch, tmp_path, capsys):
    """--strict verilirse payload.strict = True + exit 9."""
    _env(monkeypatch, tmp_path)
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
    assert rc == 9
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["strict"] is True


def test_177_mevcut_alanlar_dokunulmadi(monkeypatch, tmp_path, capsys):
    """SPEC 168 mevcut alanlar (alert/warnings/quality_warnings) AYNI."""
    _env(monkeypatch, tmp_path)
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
    assert rc == 0
    body = json.loads(capture[0]["body"])
    assert body["alert"] == "doctor"
    assert "warnings" in body
    assert "quality_warnings" in body
    # SPEC 177: yeni alan
    assert "strict" in body
    # Alan sayısı: alert + warnings + quality_warnings + strict = 4
    assert set(body.keys()) == {"alert", "warnings", "quality_warnings", "strict"}


def test_177_bulgu_yoksa_post_yok(monkeypatch, tmp_path, capsys):
    """SPEC 168 bit-uyumlu — bulgu yoksa POST atılmaz (strict alanı da yok)."""
    import atlas_core.cli as _cli
    _env(monkeypatch, tmp_path)
    monkeypatch.setattr(_cli, "_has_quality_warning", lambda _r: False)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "doctor", "--strict",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert capture == []
