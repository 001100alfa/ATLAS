"""SPEC 054 — atlas doctor --http-check URL testleri.

_check_http birim + CLI --http-check + Prometheus export.
Gerçek HTTP: `ThreadingHTTPServer` ephemeral port + kontrollü handler.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import (
    _check_http,
    _collect_doctor_report,
    _doctor_report_to_prometheus,
    main,
)


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)


def _serve(status: int = 200, body: str = "ok", delay: float = 0.0):
    """Test yardımcısı: ephemeral port HTTP server; verilen status
    döndürür. Döner: (server, thread, port, shutdown_fn).
    """
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if delay:
                time.sleep(delay)
            self.send_response(status)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode())

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

    return server, thread, port, _shutdown


# ═════════════════════════════════════════════════════════════════════
# _check_http (birim)
# ═════════════════════════════════════════════════════════════════════


def test_054_http_check_200_ok() -> None:
    """2xx → warning None, status_code=200, latency ölçüldü."""
    _, _, port, shutdown = _serve(status=200)
    try:
        result = _check_http(f"http://127.0.0.1:{port}/x")
        assert result["status_code"] == 200
        assert result["warning"] is None
        assert result["latency_ms"] is not None
        assert result["latency_ms"] >= 0
    finally:
        shutdown()


def test_054_http_check_404_warning() -> None:
    """404 → warning='HTTP 404', latency yine ölçülür."""
    _, _, port, shutdown = _serve(status=404)
    try:
        result = _check_http(f"http://127.0.0.1:{port}/x")
        assert result["status_code"] == 404
        assert result["warning"] == "HTTP 404"
        assert result["latency_ms"] is not None
    finally:
        shutdown()


def test_054_http_check_500_warning() -> None:
    _, _, port, shutdown = _serve(status=500)
    try:
        result = _check_http(f"http://127.0.0.1:{port}/x")
        assert result["status_code"] == 500
        assert "HTTP 500" in result["warning"]
    finally:
        shutdown()


def test_054_http_check_connect_refused() -> None:
    """Reachable olmayan port → connect hatası, status=None."""
    # 127.0.0.1:1 çok büyük ihtimalle reachable değil (kernel için ayrılmış)
    result = _check_http("http://127.0.0.1:1/x", timeout=1.0)
    assert result["status_code"] is None
    assert result["warning"] is not None
    assert "bağlantı hatası" in result["warning"]
    assert result["latency_ms"] is None


def test_054_http_check_gecersiz_scheme() -> None:
    result = _check_http("ftp://example.com/x")
    assert result["status_code"] is None
    assert "scheme geçersiz" in result["warning"]


def test_054_http_check_url_alani_korunur() -> None:
    """Return dict `url` alanı orijinal URL string'i taşır."""
    url = "http://127.0.0.1:1/path?q=1"
    result = _check_http(url, timeout=0.5)
    assert result["url"] == url


# ═════════════════════════════════════════════════════════════════════
# _collect_doctor_report (entegrasyon)
# ═════════════════════════════════════════════════════════════════════


def test_054_collect_report_http_check_yoksa_alan_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`--http-check` verilmezse `quality.http_check` alan YER ALMAZ."""
    _env(monkeypatch, tmp_path)
    report = _collect_doctor_report()
    assert "http_check" not in report["quality"]


def test_054_collect_report_http_check_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`http_check_url` verildiyse `quality.http_check` eklenir."""
    _env(monkeypatch, tmp_path)
    _, _, port, shutdown = _serve(status=200)
    try:
        report = _collect_doctor_report(
            http_check_url=f"http://127.0.0.1:{port}/x",
        )
        assert "http_check" in report["quality"]
        assert report["quality"]["http_check"]["status_code"] == 200
        assert report["quality"]["http_check"]["warning"] is None
    finally:
        shutdown()


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas doctor --http-check URL
# ═════════════════════════════════════════════════════════════════════


def test_054_cli_http_check_json_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    _, _, port, shutdown = _serve(status=200)
    try:
        rc = main([
            "doctor", "--json",
            "--http-check", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert "http_check" in data["quality"]
        assert data["quality"]["http_check"]["status_code"] == 200
    finally:
        shutdown()


def test_054_cli_http_check_500_strict_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """500 + --strict → exit 9 (quality warning)."""
    _env(monkeypatch, tmp_path)
    _, _, port, shutdown = _serve(status=500)
    try:
        rc = main([
            "doctor", "--strict",
            "--http-check", f"http://127.0.0.1:{port}/",
        ])
        assert rc == 9
    finally:
        shutdown()


def test_054_cli_http_check_yok_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--http-check` yoksa doctor çıktısı BİT-UYUMLU."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "http_check" not in data["quality"]


# ═════════════════════════════════════════════════════════════════════
# Prometheus export
# ═════════════════════════════════════════════════════════════════════


def test_054_prometheus_http_check_up_1() -> None:
    """2xx başarısı → `atlas_doctor_http_check_up 1` + latency gauge."""
    report = {
        "warnings": [],
        "quality": {
            "http_check": {
                "url": "http://x",
                "status_code": 200,
                "latency_ms": 12.34,
                "warning": None,
            },
        },
    }
    text = _doctor_report_to_prometheus(report)
    assert "atlas_doctor_http_check_up 1" in text
    assert "atlas_doctor_http_check_latency_ms 12.34" in text


def test_054_prometheus_http_check_up_0() -> None:
    """500/connect fail → `atlas_doctor_http_check_up 0`."""
    report = {
        "warnings": [],
        "quality": {
            "http_check": {
                "url": "http://x",
                "status_code": 500,
                "latency_ms": 5.0,
                "warning": "HTTP 500",
            },
        },
    }
    text = _doctor_report_to_prometheus(report)
    assert "atlas_doctor_http_check_up 0" in text


def test_054_prometheus_http_check_yoksa_satirlar_basilmaz() -> None:
    """http_check alanı yoksa detay metrikleri BASILMAZ."""
    report = {"warnings": [], "quality": {}}
    text = _doctor_report_to_prometheus(report)
    assert "atlas_doctor_http_check" not in text


def test_054_prometheus_latency_none_ise_satir_yok() -> None:
    """latency None (connect hatası) → up=0 var ama latency satırı yok."""
    report = {
        "warnings": [],
        "quality": {
            "http_check": {
                "url": "http://x",
                "status_code": None,
                "latency_ms": None,
                "warning": "bağlantı hatası",
            },
        },
    }
    text = _doctor_report_to_prometheus(report)
    assert "atlas_doctor_http_check_up 0" in text
    assert "atlas_doctor_http_check_latency_ms" not in text
