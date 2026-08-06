# Görev 127 — Teslim

`atlas archive --restore <id> --json` (dry-run + apply).

## Uygulama
- Dry-run: `{"mode":"dry-run","task_id","archive","target","conflict":bool}`.
- Apply: `{"mode":"apply","task_id","archive","target","restored":true}`.
- Hata → stderr SPEC HATASI + rc (2/3/6) (JSON basmaz).
- `--json` YOKSA SPEC 033/071 pretty AYNI.

## Kanıt
- +5 test; 1503 → **1508 yeşil**, mypy/ruff/scan temiz.
