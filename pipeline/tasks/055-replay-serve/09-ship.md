# Görev 055 — Teslim

`atlas replay --serve HOST:PORT` JSON HTTP endpoint + SPEC 051 refactor.

## Uygulama

- **`observability/prometheus_server.py` refactor** (bit-uyumlu):
  - `_DEFAULT_CONTENT_TYPE` sabiti.
  - `make_handler(body_fn, *, content_type=DEFAULT, allowed_paths=("/", "/metrics"))`:
    ikinci ve üçüncü parametreler keyword-only + default.
  - `serve_prometheus_http(..., content_type=DEFAULT, allowed_paths=...)`:
    yine keyword-only + default.
  - Handler class adı `_PrometheusHandler` → `_AtlasHTTPHandler`
    (Prometheus özel değil artık; SPEC 055 JSON için de kullanılır).
- **`_build_replay_json_body(limit) -> str`** (yeni):
  - `_collect_replay_runs(limit)` sonucu JSON string.
  - Her istek yeniden okur (canlı).
- **`_cmd_replay`**: yeni `--serve` dallanması ÖNCE (SPEC 057
  sıralama dersi hatırı: blocking dal önce semantik mutex).
  - `--serve + --list` → exit 2.
  - `--serve + <run-id>` → exit 2.
  - `serve_prometheus_http(host, port, body_fn,
    content_type="application/json; charset=utf-8",
    allowed_paths=("/", "/runs"))`.
- **Parser**: `--serve HOST:PORT` bayrak.

## Kanıtlar

- +10 test (`tests/test_cli_replay_serve.py`):
  - **Birim `_build_replay_json_body` (3)**: boş liste JSON dizi /
    kayıt var → dizi dolu / limit uygulanır.
  - **HTTP entegrasyon (3)**: `GET /runs` 200 + JSON + content-type,
    `GET /` de aynı, `GET /metrics` 404 (replay serve'de yalnız
    /, /runs).
  - **Mutex + hata (3)**: --serve --list exit 2, --serve <id> exit 2,
    geçersiz port exit 2.
  - **Bit-uyumluluk (1)**: --serve yoksa mevcut davranış (--list).
- SPEC 051 mevcut 26 testi BİT-UYUMLU (`_AtlasHTTPHandler` adına
  bakmıyor; sadece davranış).
- 973 → **983 yeşil**, 12 skip, cov %91.38 → %91.44.
- `uv run mypy src` temiz (31 kaynak).
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- `atlas replay --serve HOST:PORT` bayrağı.
- Yeni yardımcı `_build_replay_json_body`.
- SPEC 051 `make_handler`/`serve_prometheus_http` daha genel
  (content_type + allowed_paths parametrik).

## Değişmeyen sözleşme

- `atlas replay`, `atlas replay --list [--json] [--limit]`,
  `atlas replay <run-id> [--dry-run]` BİT-UYUMLU.
- `atlas metrics --serve`, `atlas doctor --serve` BİT-UYUMLU
  (default content-type Prometheus).
- `_collect_replay_runs(limit)` — public-ish, SPEC 028 çıktı
  sözleşmesi korunur.
