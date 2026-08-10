# Görev 182 — Teslim

`atlas archive --restore --schema [--pretty]` (SPEC 179 kalıbı restore
alt komutu için ayrı JSON şeması).

## Uygulama
- `_cmd_archive_restore` başında `--schema` kısa devre eklendi
  (SPEC 179 metrics --alert-history-show --schema kalıbı).
- **Kritik**: SPEC 149 `archive --schema` kısa devresi güncellendi —
  `--restore` verildiyse SPEC 182 dalına bırakır:
  ```python
  if args.schema and args.restore is None:  # SPEC 149
  # _cmd_archive_restore: if args.schema: ...  # SPEC 182
  ```
- Şema alanları:
  - `schema_version` = "1"
  - `dry_run_json_fields`: 5 alan (SPEC 127)
  - `apply_json_fields`: 5 alan (SPEC 127)
  - `jsonl_record_types`: 3 tip (`plan`, `restored` [yalnız --apply],
    `summary`) (SPEC 133)
  - `alert_payload_fields`: 6 alan (SPEC 176)
  - `exit_codes`: 0/2/3/6 (SPEC 033/071/176)
  - `notes`: SPEC 033/065/071/127/133/138/176/182
- Parser DEĞİŞMEDİ (--schema + --pretty zaten SPEC 149'dan).
- Arşiv/TASK_ID gerekmez (kısa devre).

## Kanıt
- +10 test (`tests/test_cli_archive_restore_schema.py`):
  1. --schema kısa devre (TASK_ID/arşiv gerekmez)
  2. dry_run_json_fields 5 alan (mode/task_id/archive/target/conflict)
  3. apply_json_fields 5 alan (mode/task_id/archive/target/restored)
  4. jsonl_record_types 3 tip (plan/restored/summary) + `restored` yalnız --apply
  5. alert_payload_fields 6 alan (SPEC 176 hepsi)
  6. exit_codes 0/2/3/6
  7. notes SPEC referansları (033/065/071/127/133/138/176/182)
  8. --pretty indent=2
  9. `archive --schema` (--restore olmadan) SPEC 149 AYNI (bit-uyumlu)
  10. --schema YOK + --restore normal davranış AYNI (arşiv yok → exit 6)
- archive regresyon 202 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 149 archive --schema JSON AYNI (--restore yoksa; SPEC 164
  sub_commands alanı korunur).
- SPEC 151 archive schema Prometheus AYNI.
- SPEC 155 archive schema Prometheus --out --gzip AYNI.
- SPEC 171 archive schema json-lines NDJSON AYNI.
- SPEC 033/065/071/127/133/138 normal restore davranışları AYNI.
- SPEC 176 alert-webhook POST tetik + payload AYNI (SPEC 182 sadece belgeler).
