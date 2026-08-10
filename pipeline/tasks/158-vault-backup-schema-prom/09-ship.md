# Görev 158 — Teslim

`atlas vault backup --schema --format prometheus` (info-metric ailesi).

## Uygulama
- `_cmd_vault_backup` --schema bloğuna `--format prometheus` dalı
  (SPEC 140/150/151/157 kalıbı).
- 4 info-metric ailesi:
  - `atlas_vault_backup_schema_version{version}`
  - `atlas_vault_backup_schema_top_level{name, type}`
  - `atlas_vault_backup_schema_exit_code{code}`
  - `atlas_vault_backup_schema_format{name, spec}`
- Parser: `--format` choices=["prometheus"] eklendi.
- Semantik MUTEX: `--format prometheus` yalnız `--schema` ile
  (normal backup modda REDDEDİR) → SPEC HATASI exit 2.
- Label escape (`\` `"` `\n`).
- notes: SPEC 158 satırı eklendi.

## Kanıt
- +8 test (`tests/test_cli_vault_backup_schema_prom.py`):
  - 4 metric HELP+TYPE.
  - version="1" etiketi.
  - top_level 6 alanı.
  - exit_codes (0, 2, 6).
  - formats yalnız human.
  - HELP+TYPE sayı 4.
  - --format YOK → JSON bit-uyumlu (SPEC 154).
  - Normal backup modda --format prometheus REDDEDİR (exit 2).
- vault_backup regresyon 82 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 154 JSON şeması AYNI (--format yoksa).
- SPEC 041/041.1/041.2/101 normal vault backup davranışı AYNI.
- Normal backup modu SPEC 158 prometheus REDDEDER (SPEC HATASI).
