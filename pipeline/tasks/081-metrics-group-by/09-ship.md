# Görev 081 — Teslim

`atlas metrics --group-by hour|day` aggregation.

## Uygulama

- `_group_records_by(records, unit)`:
  - `unit` `hour` → `YYYY-MM-DDTHH`; `day` → `YYYY-MM-DD`.
  - `ts` yok/bozuk → `"unknown"` grup.
  - Sıra: ISO lex + unknown sona.
  - Grup dict 6 alan.
- `_cmd_metrics`: `--group-by` verildiyse mevcut özet YERİNE gruplar
  tablosu; `--format prometheus` + `--alert` semantik mutex (exit 2).
- Parser: `--group-by {hour,day}` choices.

## Kanıt

- +12 test (`tests/test_cli_metrics_group_by.py`):
  - Birim (4): geçersiz unit, hour aggregation, day aggregation,
    bozuk ts unknown, deterministik sıra.
  - CLI (7): hour JSON, day insan, geçersiz argparse choices,
    --format prometheus mutex, --alert mutex, --window ortogonal,
    default bit-uyumlu.
- 1209 → **1221 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 023/029/043/051/059/064/068/076 metrics zinciri BİT-UYUMLU
  (group-by ORTOGONAL, mevcut çıktı yerine).
