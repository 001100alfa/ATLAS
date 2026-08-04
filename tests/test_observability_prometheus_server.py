"""SPEC 051 — Prometheus HTTP scrape endpoint testleri.

Birim (parse_host_port + make_handler) + entegrasyon (gerçek HTTP GET).
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.observability.prometheus_server import (
    make_handler,
    parse_host_port,
    serve_prometheus_http,
)

# ═════════════════════════════════════════════════════════════════════
# parse_host_port
# ═════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("spec,expected", [
    (":9090", ("127.0.0.1", 9090)),
    ("0.0.0.0:9090", ("0.0.0.0", 9090)),
    ("localhost:9091", ("localhost", 9091)),
    ("127.0.0.1:1", ("127.0.0.1", 1)),
    ("127.0.0.1:65535", ("127.0.0.1", 65535)),
])
def test_051_parse_host_port_gecerli(spec: str, expected: tuple[str, int]) -> None:
    assert parse_host_port(spec) == expected


@pytest.mark.parametrize("spec", [
    "9090",              # : yok
    ":abc",              # port int değil
    ":65536",            # port > 65535
    ":-1",               # negatif
])
def test_051_parse_host_port_gecersiz(spec: str) -> None:
    with pytest.raises(ValueError):
        parse_host_port(spec)


def test_051_parse_host_port_zero_ephemeral() -> None:
    """Port 0 = OS ephemeral (test/dev için kabul)."""
    assert parse_host_port(":0") == ("127.0.0.1", 0)


def test_051_parse_host_port_default_host_ozelestirilebilir() -> None:
    assert parse_host_port(":9090", default_host="0.0.0.0") == ("0.0.0.0", 9090)


# ═════════════════════════════════════════════════════════════════════
# HTTP entegrasyon — gerçek istek/response
# ═════════════════════════════════════════════════════════════════════


def _serve_in_thread(
    body_fn,
    port: int = 0,  # 0 → OS ephemeral port
) -> tuple[ThreadingHTTPServer, threading.Thread, int]:
    """Test yardımcısı: sunucuyu thread'de başlat, gerçek portu döndür."""
    handler = make_handler(body_fn)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Server hazır olsun diye kısa bekleme
    time.sleep(0.05)
    return server, thread, actual_port


def _http_get(port: int, path: str = "/metrics") -> tuple[int, str, dict[str, str]]:
    """Test yardımcısı: HTTP GET → (status, body, headers dict)."""
    url = f"http://127.0.0.1:{port}{path}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:  # noqa: S310
            body = resp.read().decode("utf-8")
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, body, headers
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace"), {}


def test_051_http_get_metrics_200(tmp_path: Path) -> None:
    """`GET /metrics` → 200 + text body + Prometheus content-type."""
    body_calls: list[int] = []

    def body_fn() -> str:
        body_calls.append(1)
        return "atlas_test_metric 42\n"

    server, thread, port = _serve_in_thread(body_fn)
    try:
        status, body, headers = _http_get(port, "/metrics")
        assert status == 200
        assert body == "atlas_test_metric 42\n"
        assert "text/plain" in headers["content-type"]
        assert "version=0.0.4" in headers["content-type"]
        assert "charset=utf-8" in headers["content-type"]
        assert len(body_calls) == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_051_http_get_root_ayni_body() -> None:
    """`GET /` de `/metrics` gibi Prometheus body döner (kolaylık)."""
    server, thread, port = _serve_in_thread(lambda: "atlas_x 1\n")
    try:
        status, body, _ = _http_get(port, "/")
        assert status == 200
        assert "atlas_x 1" in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_051_http_get_bilinmeyen_path_404() -> None:
    """`GET /foo` → 404 (yalnız /metrics ve / kabul)."""
    server, thread, port = _serve_in_thread(lambda: "x 1")
    try:
        status, _, _ = _http_get(port, "/health")
        assert status == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_051_http_body_fn_hata_500() -> None:
    """`body_fn` exception → 500 (server çökmez)."""
    def bad_body() -> str:
        raise RuntimeError("metrics.jsonl bozuk")

    server, thread, port = _serve_in_thread(bad_body)
    try:
        status, _, _ = _http_get(port, "/metrics")
        assert status == 500
        # Server hâlâ ayakta — ikinci istek de 500 ama connection kabul
        status2, _, _ = _http_get(port, "/metrics")
        assert status2 == 500
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_051_body_fn_her_istekte_yeniden_cagrilir() -> None:
    """Body producer canlı — her istek yeniden hesaplanır (scrape gereksinimi)."""
    counter = {"n": 0}

    def body_fn() -> str:
        counter["n"] += 1
        return f"atlas_calls_total {counter['n']}\n"

    server, thread, port = _serve_in_thread(body_fn)
    try:
        _, body1, _ = _http_get(port, "/metrics")
        _, body2, _ = _http_get(port, "/metrics")
        _, body3, _ = _http_get(port, "/metrics")
        assert "atlas_calls_total 1" in body1
        assert "atlas_calls_total 2" in body2
        assert "atlas_calls_total 3" in body3
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_051_serve_ready_callback_calisir() -> None:
    """`ready_cb(server)` sunucu bind edildikten sonra çağrılır."""
    captured: list[ThreadingHTTPServer] = []

    def stop_after_ready(server: ThreadingHTTPServer) -> None:
        captured.append(server)
        # ready_cb içinden shutdown yapılamaz (kilitlenir), thread'e devret
        threading.Thread(target=server.shutdown, daemon=True).start()

    serve_prometheus_http(
        "127.0.0.1", 0, lambda: "x 1",
        ready_cb=stop_after_ready,
    )
    # serve blocking — shutdown ile bitti
    assert len(captured) == 1


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas metrics --serve
# ═════════════════════════════════════════════════════════════════════


def _run_serve_and_probe(argv: list[str], probe_path: str = "/metrics") -> tuple[int, str, str]:
    """Test yardımcısı: `main(argv)` blocking çağır, thread'den probe et.

    ready_cb server'ı yakalar, urllib GET yapar, shutdown eder.
    """
    from atlas_core.observability import prometheus_server as ps

    result: dict[str, object] = {}
    real_serve = ps.serve_prometheus_http

    def wrap_serve(host, port, body_fn, **kw):
        # ready_cb enjekte et
        def ready(server):
            actual_port = server.server_address[1]
            time.sleep(0.05)
            try:
                url = f"http://127.0.0.1:{actual_port}{probe_path}"
                with urllib.request.urlopen(url, timeout=2.0) as resp:  # noqa: S310
                    result["status"] = resp.status
                    result["body"] = resp.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                result["status"] = exc.code
                result["body"] = ""
            finally:
                threading.Thread(target=server.shutdown, daemon=True).start()

        return real_serve(host, port, body_fn, ready_cb=ready, **kw)

    # monkey patch
    ps.serve_prometheus_http = wrap_serve
    try:
        rc = main(argv)
    finally:
        ps.serve_prometheus_http = real_serve
    return rc, str(result.get("body", "")), str(result.get("status", ""))


def test_051_cli_metrics_serve_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`atlas metrics --serve :0` → server açar, prometheus text servisi."""
    metrics = tmp_path / "m.jsonl"
    metrics.write_text(
        json.dumps({"ts": "t", "in": 100, "out": 50}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))

    rc, body, status = _run_serve_and_probe(["metrics", "--serve", ":0"])
    assert rc == 0
    assert status == "200"
    assert "atlas_metrics_records_total 1" in body
    assert "atlas_metrics_tokens_prompt_total 100" in body


def test_051_cli_metrics_serve_gecersiz_port_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))

    rc = main(["metrics", "--serve", ":abc"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_051_cli_metrics_json_serve_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--json --serve` argparse mutex → SystemExit(2)."""
    with pytest.raises(SystemExit) as excinfo:
        main(["metrics", "--json", "--serve", ":9090"])
    assert excinfo.value.code == 2


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas doctor --serve
# ═════════════════════════════════════════════════════════════════════


def test_051_cli_doctor_serve_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`atlas doctor --serve :0` → prometheus text servisi."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)

    rc, body, status = _run_serve_and_probe(["doctor", "--serve", ":0"])
    assert rc == 0
    assert status == "200"
    assert "atlas_doctor_up 1" in body


def test_051_cli_doctor_serve_ping_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--ping --serve` → exit 2 (her istek anthropic quota tüketir)."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)

    rc = main(["doctor", "--ping", "--serve", ":9091"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--ping ve --serve" in err


def test_051_cli_doctor_serve_format_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--format prometheus --serve` argparse mutex (aynı grup)."""
    with pytest.raises(SystemExit) as excinfo:
        main(["doctor", "--format", "prometheus", "--serve", ":9091"])
    assert excinfo.value.code == 2


def test_051_cli_doctor_serve_gecersiz_port_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)

    rc = main(["doctor", "--serve", "9090"])  # : yok
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


# ═════════════════════════════════════════════════════════════════════
# Bit-uyumluluk
# ═════════════════════════════════════════════════════════════════════


def test_051_metrics_serve_yoksa_davranis_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--serve` yoksa mevcut metrics çıktısı BİT-UYUMLU."""
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))

    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== ATLAS metrics" in out


def test_051_doctor_serve_yoksa_davranis_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--serve` yoksa mevcut doctor çıktısı BİT-UYUMLU."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)

    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== ATLAS doctor" in out
