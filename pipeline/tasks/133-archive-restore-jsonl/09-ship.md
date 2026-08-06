# Görev 133 — Teslim

`atlas archive --restore <id> --json-lines [--apply]`.

## Uygulama
- Dry-run: `plan` + `summary` (mode=dry-run).
- Apply: `plan` + `restored` + `summary` (mode=apply, restored=true).
- `--json + --json-lines` MUTEX exit 2.
- Hata → stderr, NDJSON basmaz.
- `--json-lines` YOKSA SPEC 033/127 BİT-UYUMLU.

## Kanıt
- +5 test; 1540 → **1545 yeşil**, mypy/ruff/scan temiz.
