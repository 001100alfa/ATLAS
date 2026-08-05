"""SPEC 064 — atlas metrics --alert-webhook URL testleri."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import _post_alert_webhook, main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return metrics


def _write_metrics(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


def _serve(status: int = 200, capture: list | None = None):
    """Test yardımcısı: JSON POST kabul eden ephemeral HTTP server."""
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


# ═════════════════════════════════════════════════════════════════════
# _post_alert_webhook (birim)
# ═════════════════════════════════════════════════════════════════════


def test_064_post_webhook_200_ok() -> None:
    """200 → (True, '')"""
    port, shutdown = _serve(status=200)
    try:
        ok, err = _post_alert_webhook(
            f"http://127.0.0.1:{port}/webhook",
            {"key": "value"},
        )
        assert ok is True
        assert err == ""
    finally:
        shutdown()


def test_064_post_webhook_payload_gonderilir() -> None:
    """JSON payload doğru enkod edilir + content-type başlığı."""
    captured: list = []
    port, shutdown = _serve(status=200, capture=captured)
    try:
        _post_alert_webhook(
            f"http://127.0.0.1:{port}/x",
            {"alert": "cache-hit", "hit_ratio_pct": 12.34},
        )
        assert len(captured) == 1
        req = captured[0]
        assert "application/json" in req["content_type"]
        assert "atlas-alert-webhook" in req["user_agent"]
        body = json.loads(req["body"])
        assert body["alert"] == "cache-hit"
        assert body["hit_ratio_pct"] == 12.34
    finally:
        shutdown()


def test_064_post_webhook_500_hata() -> None:
    port, shutdown = _serve(status=500)
    try:
        ok, err = _post_alert_webhook(
            f"http://127.0.0.1:{port}/", {"k": 1},
        )
        assert ok is False
        assert "HTTP 500" in err
    finally:
        shutdown()


def test_064_post_webhook_connect_hatasi() -> None:
    """Reachable olmayan port → False + bağlantı hatası."""
    ok, err = _post_alert_webhook(
        "http://127.0.0.1:1/", {"k": 1}, timeout=1.0,
    )
    assert ok is False
    assert "bağlantı hatası" in err


def test_064_post_webhook_gecersiz_scheme() -> None:
    """`file://` gibi geçersiz scheme → False + scheme hatası (SSRF)."""
    ok, err = _post_alert_webhook("file:///etc/passwd", {"k": 1})
    assert ok is False
    assert "scheme geçersiz" in err


# ═════════════════════════════════════════════════════════════════════
# CLI --alert-webhook
# ═════════════════════════════════════════════════════════════════════


def test_064_cli_alert_webhook_esik_asilinca_post(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Cache-hit 0% < eşik 50% + --alert-webhook → POST + exit 8."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    captured: list = []
    port, shutdown = _serve(status=200, capture=captured)
    try:
        rc = main([
            "metrics", "--alert", "50",
            "--alert-webhook", f"http://127.0.0.1:{port}/hooks/x",
        ])
        assert rc == 8
        assert len(captured) == 1
        body = json.loads(captured[0]["body"])
        assert body["alert"] == "cache-hit"
        assert body["hit_ratio_pct"] == 0.0
        assert body["threshold_pct"] == 50.0
        assert body["tokens_in"] == 100
        err = capsys.readouterr().err
        assert "UYARI: cache-hit" in err
        assert "[alert-webhook] POST başarılı" in err
    finally:
        shutdown()


def test_064_cli_alert_webhook_500_uyari_exit_8_korur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """POST başarısız → stderr'e; exit 8 KORUR (alert semantiği önemli)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    port, shutdown = _serve(status=500)
    try:
        rc = main([
            "metrics", "--alert", "50",
            "--alert-webhook", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 8  # KORUR
        err = capsys.readouterr().err
        assert "[alert-webhook] POST başarısız" in err
        assert "HTTP 500" in err
    finally:
        shutdown()


def test_064_cli_alert_webhook_esik_asilmadi_post_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Cache-hit yeterince yüksek → alert tetiklenmez → POST yok."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{
        "ts": "t", "in": 100, "out": 50, "cache_c": 0, "cache_r": 900,
    }])
    captured: list = []
    port, shutdown = _serve(status=200, capture=captured)
    try:
        rc = main([
            "metrics", "--alert", "50",
            "--alert-webhook", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 0
        assert len(captured) == 0  # POST hiç yapılmadı
        err = capsys.readouterr().err
        assert "[alert-webhook]" not in err
    finally:
        shutdown()


def test_064_cli_alert_webhook_email_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--alert-email + --alert-webhook ortogonal: ikisi de çalışır."""
    from atlas_core import cli as cli_mod
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])

    # SMTP monkey (gönderim başarılı)
    email_sent: list = []

    def fake_email(subj, body):
        email_sent.append(subj)
        return True, ""

    monkeypatch.setattr(cli_mod, "_send_alert_email", fake_email)

    captured: list = []
    port, shutdown = _serve(status=200, capture=captured)
    try:
        rc = main([
            "metrics", "--alert", "50",
            "--alert-email",
            "--alert-webhook", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 8
        assert len(email_sent) == 1
        assert len(captured) == 1
        err = capsys.readouterr().err
        assert "[alert-email] gönderildi" in err
        assert "[alert-webhook] POST başarılı" in err
    finally:
        shutdown()


def test_064_cli_alert_yok_webhook_etkisiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--alert yoksa --alert-webhook etkisiz."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    captured: list = []
    port, shutdown = _serve(status=200, capture=captured)
    try:
        rc = main([
            "metrics",
            "--alert-webhook", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 0
        assert len(captured) == 0
    finally:
        shutdown()
