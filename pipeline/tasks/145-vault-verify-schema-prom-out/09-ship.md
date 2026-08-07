# Görev 145 — Teslim

`atlas vault verify --schema --format prometheus --out PATH [--gzip]`.

## Uygulama
- SPEC 140 Prometheus dalına `--out` + `--gzip` desteği.
- `vs_out` + `vs_use_gzip` lokal; auto-suffix `.gz`; gzip.open("wt").
- IO hatası exit 2.

## Kanıt
- +7 test (`tests/test_cli_vault_verify_schema_prom_out.py`).
- 1609 → **1616 yeşil**, mypy/ruff/scan temiz.
