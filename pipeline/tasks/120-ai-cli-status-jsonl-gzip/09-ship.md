# Görev 120 — Teslim

`atlas ai-cli status <name> --json-lines --out --gzip`.

## Uygulama
- `--gzip` + not `--out` → SPEC HATASI exit 2.
- jsonl+out dalında `use_gzip` + `.gz` auto-suffix + `gzip.open("wt")`.
- Parser: `--gzip` action="store_true".

## Kanıt
- +6 test; 1479 → **1485 yeşil**, mypy/ruff temiz.

## Değişmeyen sözleşme
- SPEC 118 `--gzip` yoksa düz NDJSON dosya AYNI.
