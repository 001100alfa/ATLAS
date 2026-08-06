# Görev 115 — Teslim

`atlas archive --list --json --out PATH [--gzip]`.

## Uygulama
- `--out` mutex genişletildi: `--json` VEYA `--json-lines`.
- json_mode dalında `--out` → write_text (opsiyonel gzip).
- Parser'a dokunulmadı (--gzip zaten SPEC 108).

## Kanıt
- +7 test (`tests/test_cli_archive_json_out.py`).
- +1 test güncelleme (`test_cli_archive_jsonl_out.py`: eski mutex → yeni davranış).
- 1461 → **1468 yeşil**, mypy/ruff temiz.

## Değişmeyen sözleşme
- SPEC 075/098/105/108: mevcut davranışlar AYNI.
