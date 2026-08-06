# Görev 126 — Teslim

`atlas metrics --alert-history [PATH]` — alert NDJSON log.

## Uygulama
- Alert tetiklendiğinde (`hit_ratio < threshold`) NDJSON append.
- Default path: `.atlas/alert-history.jsonl` (nargs="?" const=...).
- Custom path: `--alert-history PATH`.
- Record: `{ts, alert, hit_ratio_pct, threshold_pct, records,
  tokens_in, tokens_out, cache_creation, cache_read, channels[]}`.
- `channels`: verilen bayrak listesi (email/webhook/slack).
- Parent auto-mkdir; yazma hatası → stderr UYARI + exit 8 KORUNUR.
- Alert tetiklenmezse (hit_ratio >= threshold) log yazılmaz.
- Parser: `--alert-history` nargs="?" const=".atlas/alert-history.jsonl".

## Kanıt
- +7 test (`tests/test_cli_metrics_alert_history.py`).
- 1526 → **1533 yeşil**, cov %91.44, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 029/059/064/068: alert tetikleme + kanal POST'ları AYNI.
- `--alert-history` YOKSA davranış AYNI (log yok).
