# Görev 108 — Teslim

`atlas archive --list --json-lines --out PATH --gzip`.

## Uygulama

- `_cmd_archive_list`: `--gzip` + not `--out` → SPEC HATASI exit 2.
- jsonl+out dalında `use_gzip` → `.gz` auto-suffix + `gzip.open("wt")`.
- Parser: `--gzip` action="store_true".

## Kanıt

- +7 test (`tests/test_cli_archive_jsonl_gzip.py`):
  - Auto-suffix `.gz` eklenir.
  - `.gz` uzantılı → aynen (çift YOK).
  - Decompress bit-uyumlu (düz metin ile aynı).
  - --gzip --out yok → exit 2.
  - Gzip magic 1f 8b doğrulama.
  - NDJSON her satır valid JSON.
  - --gzip YOKSA düz metin (magic yok).
- 1415 → **1422 yeşil** (+7), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 105: `--gzip` yoksa düz metin AYNI.
- SPEC 098: stdout stream (--out yoksa) AYNI.
