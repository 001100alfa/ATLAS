# Görev 187 — Teslim

`metrics --alert-webhook` payload'a `timestamp` (SPEC 032.4; SPEC 180/186 kardeşi).

## Uygulama
- SPEC 064 payload'a `timestamp: ISO 8601 seconds`.
- SPEC 169 `alert_window_minutes` yolu AYNI (bit-uyumlu).

## Kanıt
- +3 test (`tests/test_cli_metrics_webhook_timestamp.py`).
- metrics regresyon 254 test yeşil.
