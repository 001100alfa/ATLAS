# Görev 139 — Teslim

`atlas metrics --alert-history-show --json --out PATH`.

## Uygulama
- SPEC 132 alert-history-show bloğunda: `--out yok --json` MUTEX exit 2.
- json dalında `open("w")` + parent auto-mkdir + IO hatası exit 2.
- Dosya içeriği stdout modu ile BİT-UYUMLU.
- Parser DOKUNULMADI (--out zaten SPEC 096 var).

## Kanıt
- +6 test (`tests/test_cli_metrics_alert_history_show_out.py`).
- 1563 → **1569 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 132 stdout NDJSON AYNI (--out yoksa).
- SPEC 096 metrics grup prometheus --out YOLU DOKUNULMADI.
