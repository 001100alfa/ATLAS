"""SPEC 051: Prometheus text v0.0.4 HTTP scrape endpoint.

Stdlib `http.server.ThreadingHTTPServer` — dış bağımlılık YOK.
`atlas metrics --serve HOST:PORT` ve `atlas doctor --serve HOST:PORT`
komutları tarafından kullanılır.

- Yalnız `GET /` ve `GET /metrics` — diğer path'ler 404.
- Her istek `body_fn()`'i yeniden çağırır — canlı veri (metrics.jsonl
  tekrar okunur; doctor tekrar çalıştırılır).
- Access log'u sessiz (kullanıcı stderr'i temiz görsün).
- Content-Type: `text/plain; version=0.0.4; charset=utf-8`
  (Prometheus standardı).
- KeyboardInterrupt → nazikçe kapan.
"""

from __future__ import annotations

from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


def parse_host_port(spec: str, default_host: str = "127.0.0.1") -> tuple[str, int]:
    """`HOST:PORT` veya `:PORT` → `(host, port)`.

    - `":9090"` → `("127.0.0.1", 9090)` (default host = loopback)
    - `"0.0.0.0:9090"` → `("0.0.0.0", 9090)` (tüm arayüzler)
    - `"localhost:9090"` → `("localhost", 9090)`

    Raises:
        ValueError: `:` yok, port int değil veya port 0/1-65535 dışı.
    """
    if ":" not in spec:
        raise ValueError(
            f"HOST:PORT bekleniyor (ör. ':9090' veya '0.0.0.0:9090'): {spec}"
        )
    host, port_str = spec.rsplit(":", 1)
    if not host:
        host = default_host
    try:
        port = int(port_str)
    except ValueError as exc:
        raise ValueError(f"port int olmalı: {port_str}") from exc
    # Port 0 = OS ephemeral port (test/dev; gerçek scrape client'ı 0'a
    # bağlanamaz ama bind aşamasında geçerli — YAGNI extra kontrol).
    if not 0 <= port <= 65535:
        raise ValueError(f"port 0-65535 aralığında olmalı: {port}")
    return host, port


def make_handler(body_fn: Callable[[], str]) -> type[BaseHTTPRequestHandler]:
    """SPEC 051: `body_fn`'i her istek için çağıran handler sınıfı üret.

    Ayrı fonksiyon → test edilebilirlik: threading.Thread ile serve
    başlatıp handler'ı override etmeden istek yapmak mümkün.
    """

    class _PrometheusHandler(BaseHTTPRequestHandler):
        # Her istek `body_fn()` üzerinden canlı veri alır.
        server_version = "atlas-prometheus/1.0"

        def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
            if self.path not in ("/", "/metrics"):
                self.send_error(404, "Only /metrics")
                return
            try:
                body = body_fn().encode("utf-8")
            except Exception as exc:  # noqa: BLE001 - server sağlamlığı
                # HTTP status message Latin-1 (RFC 7230) — Türkçe kaçınıldı.
                # Detay body'de UTF-8 olarak döner.
                msg = f"body producer failed: {exc}".encode()
                self.send_response(500, "Internal Server Error")
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)
                return
            self.send_response(200)
            self.send_header(
                "Content-Type", "text/plain; version=0.0.4; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(  # noqa: A003 (base API)
            self, format: str, *args: Any,  # noqa: A002
        ) -> None:
            # Sessiz — kullanıcı stderr'i temiz görsün. Debug için
            # environment ile açılabilir (YAGNI).
            return

    return _PrometheusHandler


def serve_prometheus_http(
    host: str, port: int, body_fn: Callable[[], str],
    *,
    server_cls: type[ThreadingHTTPServer] = ThreadingHTTPServer,
    ready_cb: Callable[[ThreadingHTTPServer], None] | None = None,
) -> None:
    """SPEC 051: Prometheus scrape HTTP endpoint başlat (blocking).

    Args:
        host: bind adresi (loopback için `"127.0.0.1"`, tüm arayüzler
            için `"0.0.0.0"`).
        port: bind portu.
        body_fn: her istekte çağrılan text üretici (SPEC 043 kalıbı).
        server_cls: test için server sınıfı override (varsayılan
            `ThreadingHTTPServer` — eşzamanlı istek desteği).
        ready_cb: server bind edildikten sonra çağrılan opsiyonel
            callback (test/monitör; None → yalnız stdout log).

    KeyboardInterrupt ile nazikçe kapanır.
    """
    import threading

    handler = make_handler(body_fn)
    server = server_cls((host, port), handler)
    actual_port = server.server_address[1]
    print(
        f"[serve] Prometheus scrape hazır: http://{host}:{actual_port}/metrics"
    )
    print("        Durdurmak için Ctrl+C.")
    # ready_cb'yi ayrı thread'de çağır — serve_forever() ana thread'de
    # accept döngüsünü başlatabilsin. Aksi hâlde ready_cb içinden gelen
    # client isteği kabul edilmez (server socket dinler ama accept YOK).
    if ready_cb is not None:
        threading.Thread(
            target=ready_cb, args=(server,), daemon=True,
        ).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve] Ctrl+C — kapanıyor…")
    finally:
        server.server_close()
