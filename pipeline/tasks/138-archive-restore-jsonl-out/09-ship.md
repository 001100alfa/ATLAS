# Görev 138 — Teslim

`atlas archive --restore <id> --json-lines --out PATH [--apply]`.

## Uygulama
- `_cmd_archive_restore`: `restore_out_arg` + not jsonl → exit 2.
- `_restore_emit_lines(records)` lokal helper — stdout ya da PATH'e yaz.
- Parent auto-mkdir; IO hatası exit 2.
- Hata durumu (RestoreError) → dosya YAZILMAZ (early return).
- Parser docstring: SPEC 105/138 (mevcut --out yeniden kullanıldı).

## Kanıt
- +8 test (`tests/test_cli_archive_restore_jsonl_out.py`).
- 1569 → **1577 yeşil**, mypy/ruff/scan temiz.
