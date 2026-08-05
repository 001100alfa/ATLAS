# Görev 087 — Teslim

`atlas vault verify --format {human,json,json-pretty,json-lines}`.

## Uygulama

- `_cmd_vault_verify`: MUTEX ön-kontrol (`--format` + `--json`/`--pretty`
  → exit 2 SPEC HATASI).
- `--format json-lines` streaming çıktı:
  - `{"type":"broken_link","from":..,"to":..}` × N
  - `{"type":"orphan_note","note":..}` × N
  - `{"type":"orphan_tag","tag":..}` × N
  - Son satır `{"type":"summary", ...}` (temiz vault → tek satır summary).
- `--format json` = `--json` içerik AYNI (tek satır).
- `--format json-pretty` = `--json --pretty` içerik AYNI (indent=2).
- `--format human` → mevcut human dalı.
- `--format` VERİLMEZSE SPEC 042 BİT-UYUMLU (mevcut `--json`/`--pretty`
  yolu). `--strict` (exit 4) ve `--dump-report` (yan etki) format'tan
  bağımsız çalışır.
- Parser: `--format` choices=[human, json, json-pretty, json-lines],
  default None. Geçersiz → argparse SystemExit(2).

## Kanıt

- +10 test (`tests/test_cli_vault_verify_jsonl.py`):
  - Basic stream (3 broken + orfan → satır sayı + summary).
  - Temiz vault → sadece summary satırı, clean=True.
  - Her satır tek başına valid JSON (NDJSON kontratı).
  - `--format json` bit-uyumlu (tek satır).
  - `--format json-pretty` indent'li.
  - `--format` + `--json` MUTEX exit 2.
  - `--format` + `--pretty` MUTEX exit 2.
  - Geçersiz choice → argparse SystemExit(2).
  - `--format json-lines --strict` → bulgu varsa exit 4.
  - `--format` yoksa + `--json` bit-uyumlu (SPEC 042).
- 1244 → **1254 yeşil** (+10), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 042: `--format` VERİLMEZSE davranış AYNI (mevcut --json/--pretty
  yolu). Human çıktı, --strict exit 4, --dump-report yan etki AYNI.
- SPEC 052 dump-report format'tan bağımsız.
