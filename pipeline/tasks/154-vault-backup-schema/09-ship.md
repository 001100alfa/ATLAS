# Görev 154 — Teslim

`atlas vault backup --schema [--pretty]`.

## Uygulama
- `_cmd_vault_backup` başında `--schema` kısa devre (SPEC 040/136/146/149 kalıbı).
- Vault dizini gerekmez; JSON şema tanımı basılır.
- 6 top_level alan (backup çıktı yapısı):
  - backup_path (SPEC 041), vault_root, action (backup | backup-auto),
    split_parts (SPEC 101 opsiyonel), pruned_count (SPEC 041.1 opsiyonel),
    encrypted (SPEC 041.2 opsiyonel).
- exit_codes 0/2/6 (SPEC 041/041.1).
- formats human (default; --json henüz yok — YAGNI).
- notes: SPEC 041/041.1/041.2/101/154 referansları.
- Parser: `--schema` + `--pretty` eklendi.

## Kanıt
- +7 test (`tests/test_cli_vault_backup_schema.py`):
  - schema kısa devre + dizin gerekmez
  - 6 top_level alan
  - 3 exit_code (0/2/6)
  - formats yalnız human
  - notes SPEC referansları (041/041.1/041.2/101/154)
  - --pretty indent=2
  - --schema YOKSA SPEC 041 dizin yok hatası (bit-uyumlu)
- vault_backup regresyon 74 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 041 normal vault backup davranışı AYNI (`--schema` yoksa).
- SPEC 041.1 --auto/--keep/audit action DOKUNULMADI.
- SPEC 041.2 --encrypt/--recipient DOKUNULMADI.
- SPEC 101 --split DOKUNULMADI.
- SPEC 067 --keep-encrypted DOKUNULMADI.
