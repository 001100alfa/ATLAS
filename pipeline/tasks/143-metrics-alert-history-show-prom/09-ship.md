# Görev 143 — Teslim

`atlas metrics --alert-history-show --format prometheus` (info-metric counter).

## Uygulama
- SPEC 132 alert-history-show bloğuna --format prometheus dalı.
- 3 metric ailesi:
  - `atlas_metrics_alert_history_total` (counter) — toplam log kayıt.
  - `atlas_metrics_alert_history_recent` (counter) — --limit tail sayısı.
  - `atlas_metrics_alert_channel_total{channel}` (counter) — kanal başına.
- Kanallar alfabetik lex sıra (deterministik).
- `--format prometheus` YOKSA SPEC 132 pretty/JSON AYNI.
- `--format + --json` argparse mutex (SPEC 047 grup kalıbı) hâlâ geçerli.

## Kanıt
- +7 test (`tests/test_cli_metrics_alert_history_show_prom.py`).
- 1581 → **1588 yeşil**, mypy/ruff/scan temiz.
