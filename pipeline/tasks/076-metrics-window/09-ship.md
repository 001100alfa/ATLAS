# Görev 076 — Teslim

`atlas metrics --window MINUTES` — time-based filtre.

## Uygulama

- `_filter_records_by_window(records, window_minutes, now=None)`:
  `ts` ISO parse; `now - MINUTES` sonrası kayıt. `ts` yok/bozuk → dahil.
  `window_minutes=None` → orijinal liste.
- `_cmd_metrics`: `--window` bayrağı; `<=0` → exit 2. Records filtre
  edilir, sonra `[-limit:]` slice (ortogonal).
- Parser: `--window MINUTES` (float).

## Kanıt

- +10 test (`tests/test_cli_metrics_window.py`):
  - Birim (4): None filtre yok, 5dk pencere eski atılır, hepsi yeni
    hepsi dahil, ts yok/bozuk nazik dahil.
  - CLI (6): window filtresi doğrulama, geçersiz 0 exit 2, negatif
    exit 2, window+limit ortogonal, window yoksa bit-uyumlu, --json
    uyumlu.
- 1123 → **1133 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 023/029/043/051/059/064/068 hepsi BİT-UYUMLU (window ortogonal).
- Prometheus text (`_build_metrics_prometheus_text`) DEĞİŞMEDİ (live
  scrape için `limit` yeterli; window YAGNI).
