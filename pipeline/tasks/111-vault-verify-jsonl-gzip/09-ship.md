# Görev 111 — Teslim

`atlas vault verify --format json-lines --out --gzip`.

## Uygulama

- `_cmd_vault_verify`: `--gzip` + not `--out` → SPEC HATASI exit 2.
- json-lines dalında `out_fh` üretimi: `--gzip` ise
  `gzip.open(op, "wt")` (auto `.gz` suffix). `--gzip` yoksa
  `op.open("w")` (SPEC 092 BİT-UYUMLU).
- `out_fh: Any` (mypy: gzip file vs text file union).
- Parser: `--gzip` action="store_true".

## Kanıt

- +7 test (`tests/test_cli_vault_verify_jsonl_gzip.py`):
  - Auto-suffix `.gz` eklenir.
  - Decompress → düz NDJSON BİT-UYUMLU.
  - --gzip --out yok → exit 2.
  - Gzip magic 1f 8b doğrulama.
  - --strict + bulgu + gzip → exit 4, dosyaya yazılır.
  - NDJSON her satır valid JSON.
  - --gzip YOKSA düz metin.
- 1436 → **1443 yeşil** (+7), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 092: --gzip yoksa düz NDJSON dosya AYNI.
- SPEC 087/042: stdout stream + strict + dump-report AYNI.
