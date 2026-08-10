# Görev 150 — Teslim

`atlas ai-cli status --schema --format prometheus` (info-metric ailesi).

## Uygulama
- `_cmd_ai_cli_status` --schema bloğuna `--format prometheus` dalı (SPEC 140 kalıbı).
- 4 info-metric ailesi:
  - `atlas_ai_cli_status_schema_version{version}`
  - `atlas_ai_cli_status_schema_top_level{name, type}`
  - `atlas_ai_cli_status_schema_exit_code{code}`
  - `atlas_ai_cli_status_schema_format{name, spec}`
- Parser: `--format` choices=["prometheus"] eklendi.
- Semantik MUTEX: `--format prometheus` yalnız `--schema` ile
  (normal status modda REDDEDİR) → SPEC HATASI exit 2.
- Label escape (`\` `"` `\n`).
- notes: SPEC 150 satırı eklendi.

## Kanıt
- +8 test (`tests/test_cli_ai_cli_status_schema_prom.py`):
  - 4 metric HELP+TYPE.
  - version="1" etiketi.
  - top_level 8 alanı (name, installed_version, declared_version,
    up_to_date, install_dir, size_bytes, size_human, bin_path).
  - exit_codes (0, 2, 4).
  - formats (human, json, json-lines).
  - HELP+TYPE sayı 4.
  - --format YOK → JSON bit-uyumlu (SPEC 146).
  - Normal status modda --format prometheus REDDEDİR (exit 2).
- ai-cli status regresyon 28 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 146 JSON şeması AYNI (--format yoksa).
- SPEC 037.4 normal `status <name>` davranışı AYNI (name verildiğinde).
- SPEC 118/120 --json-lines/--out/--gzip DOKUNULMADI.
- Normal status modu SPEC 150 prometheus REDDEDER (SPEC HATASI).
