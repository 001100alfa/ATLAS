# Görev 136 — Teslim

`atlas vault verify --schema [--pretty]`.

## Uygulama
- `_cmd_vault_verify` başında --schema kısa devre (SPEC 040 kalıbı).
- Vault dizini gerekmez; JSON: `{schema_version, top_level, exit_codes,
  formats, notes}`.
- 4 format (human/json/json-pretty/json-lines) tanımı içerir.
- `--pretty` indent=2.
- Parser: `--schema` action="store_true".

## Kanıt
- +6 test; +6 → **1559 yeşil**, mypy/ruff temiz.
