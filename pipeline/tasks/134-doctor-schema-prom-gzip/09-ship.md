# Görev 134 — Teslim

`atlas doctor --schema --format prometheus --out PATH [--gzip]`.

## Uygulama
- --schema Prometheus dalında `schema_out` / `schema_gzip` locale değişkenleri.
- `--gzip` + not `--out` → exit 2.
- Auto-suffix `.gz`; `gzip.open("wt")` (SPEC 103/114 kalıbı).
- --schema JSON modu (--format yok) + --out → SPEC HATASI exit 2.
- --schema JSON + --gzip → SPEC HATASI exit 2.
- Parser'a dokunulmadı (--out ve --gzip zaten SPEC 110/114 var).

## Kanıt
- +7 test (`tests/test_cli_doctor_schema_prom_out.py`).
- 1533 → **1540 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 128 stdout Prometheus AYNI (--out yoksa).
- SPEC 040 JSON AYNI (--format yoksa).
- SPEC 110/114 diff-history-all yolu AYNI (mutex önden kısa devre).
