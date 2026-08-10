# Görev 151 — Teslim

`atlas archive --schema --format prometheus` (info-metric ailesi).

## Uygulama
- `_cmd_archive` --schema bloğuna `--format prometheus` dalı (SPEC 140/150 kalıbı).
- 4 info-metric ailesi:
  - `atlas_archive_schema_version{version}`
  - `atlas_archive_schema_top_level{name, type}`
  - `atlas_archive_schema_exit_code{code}`
  - `atlas_archive_schema_format{name, spec}`
- Parser: `--format` choices=["prometheus"] eklendi.
- Semantik MUTEX: `--format prometheus` yalnız `--schema` ile
  (normal archive modda REDDEDİR) → SPEC HATASI exit 2.
- Label escape (`\` `"` `\n`).
- notes: SPEC 151 satırı eklendi.

## Kanıt
- +8 test (`tests/test_cli_archive_schema_prom.py`):
  - 4 metric HELP+TYPE.
  - version="1" etiketi.
  - top_level 7 alanı (archive, task_id, date, size_bytes,
    size_human, member_count, mtime).
  - exit_codes (0, 2, 3, 6).
  - formats (human, json, json-lines).
  - HELP+TYPE sayı 4.
  - --format YOK → JSON bit-uyumlu (SPEC 149).
  - Normal archive --list modda --format prometheus REDDEDİR (exit 2).
- archive regresyon 30 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 149 JSON şeması AYNI (--format yoksa).
- SPEC 007/012/033/065/071/075: archive normal komutları AYNI.
- SPEC 105/108/127/133/138 --out/--gzip/--restore DOKUNULMADI.
- Normal archive modu SPEC 151 prometheus REDDEDER (SPEC HATASI).
