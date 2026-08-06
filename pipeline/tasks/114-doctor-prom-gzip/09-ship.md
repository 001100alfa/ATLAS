# Görev 114 — Teslim

`atlas doctor --diff-history-all --format prometheus --out --gzip`.

## Uygulama
- `--gzip` + not `--out` → SPEC HATASI exit 2.
- Prometheus `--out` dalında `use_gzip_doc` + `.gz` auto-suffix + `gzip.open`.
- Değişken adı `doc_text` (mypy scope temiz).
- Parser: `--gzip` action="store_true".

## Kanıt
- +6 test (`tests/test_cli_doctor_prom_gzip.py`): auto-suffix, decompress
  bit-uyumlu, --out yok mutex, magic bytes, `.gz` uzantı aynen, --gzip
  yok düz metin.
- 1451 → **1457 yeşil** (+6), 12 skip.
- mypy/ruff temiz.
