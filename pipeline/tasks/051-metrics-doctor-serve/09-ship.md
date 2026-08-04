# Görev 051 — Teslim

`atlas metrics --serve` + `atlas doctor --serve` HTTP scrape endpoint.

## Uygulama

- **Yeni namespace**: `src/atlas_core/observability/`
- **Yeni modül**: `observability/prometheus_server.py`
  - `parse_host_port(spec, default_host="127.0.0.1")` — `:PORT` +
    `HOST:PORT` parse; port 0-65535 (0 = ephemeral).
  - `make_handler(body_fn)` — her istekte `body_fn()` yeniden çağrılır.
    `GET / | /metrics` → 200 + `text/plain; version=0.0.4; charset=utf-8`.
    Diğer path'ler 404. `body_fn()` exception → 500 (UTF-8 body).
    Access log sessiz.
  - `serve_prometheus_http(host, port, body_fn, *, server_cls, ready_cb)` —
    `ThreadingHTTPServer` bind + `serve_forever` blocking. `ready_cb`
    AYRI thread'de çağrılır (accept döngüsü main thread'de kalabilsin).
    Ctrl+C nazikçe kapan.
- **`_build_metrics_prometheus_text(limit) -> str`**: SPEC 043 çıktı
  mantığı fonksiyona çıkarıldı (print YOK). Her scrape'te tekrar okur.
- **`_cmd_metrics`**: yeni `--serve HOST:PORT` bayrağı, `_json`+`_format`
  ile mutex.
- **`_cmd_doctor`**: yeni `--serve HOST:PORT` bayrağı; `_ping` ile
  ek exit-2 mutex; `_collect_doctor_report()` her scrape'te tekrar.

## Kanıtlar

- +26 test (`tests/test_observability_prometheus_server.py`):
  - **Birim (7)**: `parse_host_port` geçerli x5 + geçersiz x4 +
    default_host + zero_ephemeral.
  - **HTTP entegrasyon (6)**: `GET /metrics` 200 + content-type,
    `GET /` aynı body, 404, `body_fn` exception → 500, `body_fn` her
    istekte yeniden, `ready_cb` çağrılır.
  - **CLI metrics --serve (3)**: server açılır + gerçek HTTP GET +
    Prometheus text; geçersiz port exit 2; `--json --serve` argparse
    mutex.
  - **CLI doctor --serve (4)**: server açılır + `atlas_doctor_up 1`;
    `--ping --serve` exit 2 (semantik mutex); `--format --serve`
    argparse mutex; geçersiz port exit 2.
  - **Bit-uyumluluk (2)**: `metrics` bayraksız + `doctor` bayraksız
    korunur.
- Mevcut 91 test (metrics + doctor + strict) BİT-UYUMLU.
- 886 → **912 yeşil**, 12 skip, cov %91.21 → %91.18 (yeni HTTP
  server kodu %100 kapsanmıyor — timeout/edge dalları test dışı).
- `uv run mypy src` temiz (31 kaynak dosya).
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Yeni CLI bayrakları: `atlas metrics --serve HOST:PORT`,
  `atlas doctor --serve HOST:PORT`.
- Yeni exit 2 nedeni: `doctor --ping --serve` (semantik mutex).

## Değişmeyen sözleşme

- `atlas metrics` mevcut çıktıları (bayraksız, `--json`, `--format
  prometheus`, `--alert`) BİT-UYUMLU.
- `atlas doctor` mevcut çıktıları (bayraksız, `--json`, `--schema`,
  `--format`, `--strict`, `--scan-src`, `--ping`, `--pretty`)
  BİT-UYUMLU.
- Prometheus text çıktı formatı (SPEC 043 + 047) BİT-UYUMLU — sadece
  transport değişti (stdout → HTTP).
