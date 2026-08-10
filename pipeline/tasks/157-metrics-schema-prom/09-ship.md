# Görev 157 — Teslim

`atlas metrics --schema --format prometheus` (info-metric ailesi).

## Uygulama
- `_cmd_metrics` --schema bloğuna `--format prometheus` dalı (SPEC 140/150/151 kalıbı).
- 4 info-metric ailesi:
  - `atlas_metrics_schema_version{version}`
  - `atlas_metrics_schema_top_level{name, type}`
  - `atlas_metrics_schema_exit_code{code}`
  - `atlas_metrics_schema_format{name, spec}`
- Label escape (`\` `"` `\n`).
- notes: SPEC 157 satırı eklendi.

## Kanıt
- +8 test (`tests/test_cli_metrics_schema_prom.py`):
  - 4 metric HELP+TYPE.
  - version="1" etiketi.
  - top_level 7 alanı (ts, in, out, cache_c, cache_r, cost, inflight).
  - exit_codes (0, 2, 4, 8).
  - formats (human, json, prometheus).
  - HELP+TYPE sayı 4.
  - --format YOK → JSON bit-uyumlu (SPEC 153).
  - --schema YOK + --format prometheus normal SPEC 043 davranışı AYNI.
- metrics_schema regresyon 15 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 153 JSON şeması AYNI (--format yoksa).
- SPEC 023/029/043 normal metrics davranışı AYNI (`--schema` yoksa).
- Parser DOKUNULMADI (--format ve --schema zaten mevcut).
