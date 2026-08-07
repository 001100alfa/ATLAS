# Görev 140 — Teslim

`atlas vault verify --schema --format prometheus` (info-metric ailesi).

## Uygulama
- `_cmd_vault_verify` --schema bloğuna `--format prometheus` dalı.
- 4 info-metric ailesi (SPEC 128 kalıbı):
  - `atlas_vault_verify_schema_version{version}`
  - `atlas_vault_verify_schema_top_level{name, type}`
  - `atlas_vault_verify_schema_exit_code{code}`
  - `atlas_vault_verify_schema_format{name, spec}`
- Parser: `--format` choices'a `prometheus` eklendi.
- Semantik MUTEX: `--format prometheus` yalnız `--schema` ile
  (normal verify modda prometheus çıktı YOK) → SPEC HATASI exit 2.
- Tip: `schema: dict[str, Any]` (mypy narrow için).
- notes: SPEC 140 satırı eklendi.

## Kanıt
- +8 test (`tests/test_cli_vault_verify_schema_prom.py`):
  - 4 metric HELP+TYPE.
  - version="1" etiketi.
  - top_level alanları (notes_total, broken_links, ...).
  - exit_codes (0, 2, 4).
  - formats (human, json, json-pretty, json-lines).
  - HELP+TYPE sayı 4.
  - --format YOK → JSON bit-uyumlu.
  - Vault dizini olmasa da çalışır (kısa devre).
- 1594 → **1602 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 136 JSON şeması AYNI (--format yoksa).
- SPEC 087 --format seçenekleri (human/json/json-pretty/json-lines) AYNI.
- Normal verify modu SPEC 140 prometheus REDDEDER (SPEC HATASI).
