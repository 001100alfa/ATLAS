"""SPEC 068 — atlas metrics --alert-slack URL testleri."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main


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
    """Slack-benzeri incoming webhook mock."""
    class _H(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            n = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(n) if n else b""
            if capture is not None:
                capture.append({
                    "body": body.decode("utf-8"),
                    "content_type": self.headers.get("Content-Type"),
                })
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_a, **_kw):  # noqa: A003
            return

    srv = ThreadingHTTPServer(("127.0.0.1", 0), _H)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)

    def _shutdown():
        srv.shutdown()
        srv.server_close()
        t.join(timeout=2.0)
    return port, _shutdown


# ═════════════════════════════════════════════════════════════════════
# CLI: --alert-slack
# ═════════════════════════════════════════════════════════════════════


def test_068_cli_alert_slack_payload_text_formati(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Payload `{text: ...}` Slack incoming webhook uyumlu format."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    captured: list = []
    port, shutdown = _serve(status=200, capture=captured)
    try:
        rc = main([
            "metrics", "--alert", "50",
            "--alert-slack", f"http://127.0.0.1:{port}/services/T/B/xyz",
        ])
        assert rc == 8
        assert len(captured) == 1
        body = json.loads(captured[0]["body"])
        # Slack: `{text}` alanı zorunlu
        assert "text" in body
        assert "ATLAS cache-hit alert" in body["text"]
        assert "records:" in body["text"]
        # `{text}` DIŞINDA başka alan olmamalı (Slack MVP wrapper)
        assert set(body.keys()) == {"text"}
        err = capsys.readouterr().err
        assert "[alert-slack] POST başarılı" in err
    finally:
        shutdown()


def test_068_cli_alert_slack_500_uyari_exit_8_korur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    port, shutdown = _serve(status=500)
    try:
        rc = main([
            "metrics", "--alert", "50",
            "--alert-slack", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 8  # KORUR
        err = capsys.readouterr().err
        assert "[alert-slack] POST başarısız" in err
        assert "HTTP 500" in err
    finally:
        shutdown()


def test_068_cli_alert_slack_esik_asilmadi_post_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{
        "ts": "t", "in": 100, "out": 50, "cache_c": 0, "cache_r": 900,
    }])
    captured: list = []
    port, shutdown = _serve(status=200, capture=captured)
    try:
        rc = main([
            "metrics", "--alert", "50",
            "--alert-slack", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 0
        assert len(captured) == 0
    finally:
        shutdown()


def test_068_cli_alert_slack_webhook_email_uc_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Slack + Webhook + Email üçü aynı çağrıda: hepsi çalışır (ortogonal)."""
    from atlas_core import cli as cli_mod
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    email_sent: list = []
    monkeypatch.setattr(cli_mod, "_send_alert_email",
                        lambda s, b: (email_sent.append(s), (True, ""))[1])
    captured_wh: list = []
    port_wh, sh_wh = _serve(status=200, capture=captured_wh)
    captured_sl: list = []
    port_sl, sh_sl = _serve(status=200, capture=captured_sl)
    try:
        rc = main([
            "metrics", "--alert", "50",
            "--alert-email",
            "--alert-webhook", f"http://127.0.0.1:{port_wh}/",
            "--alert-slack", f"http://127.0.0.1:{port_sl}/",
        ])
        assert rc == 8
        assert len(email_sent) == 1
        assert len(captured_wh) == 1
        assert len(captured_sl) == 1
        # Payload'lar farklı formatta (webhook = ATLAS ham; slack = {text})
        wh_body = json.loads(captured_wh[0]["body"])
        sl_body = json.loads(captured_sl[0]["body"])
        assert wh_body.get("alert") == "cache-hit"  # ATLAS ham
        assert "text" in sl_body                      # Slack özel
        assert "alert" not in sl_body                 # Slack ham DEĞİL
    finally:
        sh_wh()
        sh_sl()


def test_068_cli_alert_yok_slack_etkisiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--alert yoksa --alert-slack etkisiz."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    captured: list = []
    port, shutdown = _serve(status=200, capture=captured)
    try:
        rc = main([
            "metrics",
            "--alert-slack", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 0
        assert len(captured) == 0
    finally:
        shutdown()
