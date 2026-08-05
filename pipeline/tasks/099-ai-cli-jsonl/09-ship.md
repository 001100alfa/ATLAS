# Görev 099 — Teslim

`atlas ai-cli list --outdated --json-lines`.

## Uygulama

- `_cmd_ai_cli_list`: `jsonl_mode` bayrağı.
- MUTEX ön-kontrol:
  - `--json-lines` + not `--outdated` → exit 2.
  - `--json-lines` + `--json` → exit 2.
- NDJSON çıktı:
  - Her paket: `{"name","expected","installed"}` (SPEC 088 alanlar).
  - Son satır: `{"type":"summary","path","outdated","total_deps"}`.
- `--strict` ile ORTOGONAL — exit 4 döner, NDJSON hâlâ basılır.
- `total_deps` sayısı filtreden ÖNCE (tam deps).
- Parser: `--json-lines` action="store_true".

## Kanıt

- +7 test (`tests/test_cli_ai_cli_outdated_jsonl.py`):
  - 2 outdated + 1 summary satır sayı doğrulama.
  - Temiz → yalnız summary (outdated=0).
  - Paket alanları SPEC 088 ile AYNI.
  - --outdated yok → exit 2.
  - --json + --json-lines MUTEX exit 2.
  - --strict + bulgu → exit 4, NDJSON basılır.
  - --json-lines yoksa SPEC 088 bit-uyumlu.
- 1321 → **1328 yeşil** (+7), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 088: `--outdated --json` çıktı AYNI.
- SPEC 094: `--strict` davranışı AYNI.
- Yalın `list` (SPEC 037.2) DOKUNULMADI.
