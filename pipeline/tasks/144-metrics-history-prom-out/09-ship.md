# Görev 144 — Teslim

`atlas metrics --alert-history-show --format prometheus --out PATH [--gzip]`.

## Uygulama
- SPEC 143 Prometheus dalına `--out` + `--gzip` desteği (SPEC 096/134 kalıbı).
- `ah_out` + `ah_use_gzip` lokal; auto-suffix `.gz`; gzip.open("wt").
- `--gzip` --out yok → SPEC HATASI exit 2.
- IO hatası → exit 2.
- SPEC 139 mesajı güncellendi (`--json` VEYA `--format prometheus`).

## Kanıt
- +7 test (`tests/test_cli_metrics_alert_history_show_prom_out.py`).
- 1602 → **1609 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 143 stdout AYNI (--out yoksa).
- SPEC 139 JSON --out yolu AYNI.
