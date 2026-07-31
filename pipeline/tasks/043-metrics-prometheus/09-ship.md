# Görev 043 — Teslim

`atlas metrics --format prometheus` — scrape edilebilir metric export.

## Uygulama

- `atlas_core/cli.py::_cmd_metrics`:
  - Yeni fmt branch: `elif fmt == "prometheus":` — v0.0.4 text çıktısı.
  - Cost tahmini fiyat env'i yoksa 0.0 olarak yayımlanır (satır atlanmaz —
    Prometheus için tutarlılık; monotonik counter beklenir).
  - inflight satırları yalnız SPEC 023.2 tüketiciyle uyumlu şekilde
    veri varsa basılır.
  - Savunma: `--json + --format prometheus` env'e karşı ek exit 2
    (argparse mutex zaten yakalıyor ama defense-in-depth).
- Parser: `p_met_out = add_mutually_exclusive_group()` ile `--json` ve
  `--format {human,prometheus}` mutex; `--format` default `None` →
  bit-uyumluluk.

## Kanıtlar

- +6 test (tests/test_cli_metrics.py `test_043_*`):
  - Prometheus temel çıktı (records/tokens/cache/hit_ratio/cost)
  - inflight yoksa satır YOK
  - inflight varsa avg=2.0 max=3
  - `--json --format prometheus` argparse SystemExit(2)
  - default (bayraksız) SPEC 023 insan bit-uyumlu (prometheus sızmıyor)
  - `--format human` = default davranış
- 804 → **810 yeşil, 12 skip, cov %90.85**.
- `uv run mypy src` temiz; `uv run ruff check src tests` temiz;
  `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Yeni bayrak: `atlas metrics --format {human,prometheus}` (mutex `--json`).
- Yeni metric adları (9 tanesi; inflight_* iki koşullu).

## Değişmeyen sözleşme

- `atlas metrics` (bayraksız) bit-uyumlu.
- `atlas metrics --json` bit-uyumlu (ham liste).
- `atlas metrics --alert PCT` bit-uyumlu (alert semantiği format
  bağımsız — insan çıktısıyla verilirse ve eşik aşılırsa exit 8).
