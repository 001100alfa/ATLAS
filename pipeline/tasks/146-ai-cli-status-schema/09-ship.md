# Görev 146 — Teslim

`atlas ai-cli status [--schema] [--pretty]`.

## Uygulama
- `_cmd_ai_cli_status` en başında `--schema` kısa devre (SPEC 040/136 kalıbı).
- Vault/package.json dokunmaz; JSON şema tanımı basar.
- 8 top_level alan + 3 exit_code + 3 format (human/json/json-lines).
- `name` positional `nargs="?"` — --schema ile birlikte opsiyonel.
- --schema yoksa name zorunlu → SPEC HATASI exit 2.
- Parser: `--schema` + `--pretty` eklendi.

## Kanıt
- +7 test (`tests/test_cli_ai_cli_status_schema.py`).
- 1622 → **1629 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 037.4 normal status davranışı AYNI (name verildiğinde).
- SPEC 118/120 --json-lines/--out/--gzip DOKUNULMADI.
