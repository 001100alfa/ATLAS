# Görev 109 — Teslim

`atlas ai-cli list --outdated --json-lines --out --gzip`.

## Uygulama

- `_cmd_ai_cli_list`: `--gzip` + not `--out` → SPEC HATASI exit 2.
- jsonl dalında `use_gzip` + `_pkg_line(p)` yardımcı lambda.
- gzip.open("wt") + `.gz` auto-suffix (SPEC 103/108 kalıbı).
- `--strict` ile ORTOGONAL (exit 4 korunur).
- Parser: `--gzip` action="store_true".

## Kanıt

- +6 test (`tests/test_cli_ai_cli_jsonl_gzip.py`):
  - Auto-suffix `.gz` eklenir.
  - Decompress → düz NDJSON BİT-UYUMLU.
  - --gzip --out yok → exit 2.
  - Gzip magic 1f 8b doğrulama.
  - --strict + bulgu → exit 4, gzip'e yazılır.
  - --gzip YOKSA düz metin.
- 1422 → **1428 yeşil** (+6), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 106: `--gzip` yoksa düz NDJSON dosya AYNI.
- SPEC 099/094: stdout stream + strict davranışları AYNI.
