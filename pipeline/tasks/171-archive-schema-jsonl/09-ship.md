# Görev 171 — Teslim

`atlas archive --schema --format json-lines [--out PATH [--gzip]]`.

## Uygulama
- `_cmd_archive` --schema bloğuna `--format json-lines` dalı eklendi
  (SPEC 087/126/166 NDJSON kalıbı, SPEC 151 Prometheus dalı ile paralel).
- NDJSON stream: her top_level/exit_code/format/sub_command bir satır +
  son satır summary (count'lar dahil).
- SPEC 164 `sub_commands` NDJSON satırlarına yansır (list/restore/search/all).
- `--out PATH [--gzip]` desteği (SPEC 155/166 kalıbı).
- MUTEX: `--format json-lines` yalnız `--schema` ile — normal archive
  modda REDDEDİR (SPEC HATASI exit 2, SPEC 151/158/166 kalıbı).
- Parser: `--format` choices'a `json-lines` eklendi (mevcut prometheus'a).

## Kanıt
- +9 test (`tests/test_cli_archive_schema_jsonl.py`):
  1. NDJSON stream — son satır summary + tip çeşitliliği
  2. summary sayıları stream tip dağılımına eşit
  3. sub_command satırlarında name/exit_codes/spec (SPEC 164 restore=0/2/3/6)
  4. --out ile PATH'e stream + stdout boş
  5. --gzip auto-suffix .gz + gzip.open ile okunabilir
  6. --gzip --out olmadan SPEC HATASI exit 2
  7. Normal archive + --format json-lines SPEC HATASI (yeni MUTEX)
  8. --format YOK → SPEC 149 JSON default bit-uyumlu (sub_commands dahil)
  9. SPEC 151 Prometheus çıktısı DOKUNULMADI
- archive schema/list regresyon 81 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 149 JSON default AYNI (--format yoksa).
- SPEC 151 Prometheus çıktısı AYNI (yeni json-lines ayrı dal).
- SPEC 155 --out --gzip yolu (Prometheus için) AYNI.
- SPEC 164 sub_commands JSON'da AYNI + json-lines'a taşındı (bit-uyumlu ekleme).
- SPEC 007/012/033/065/071/075 normal archive komutları AYNI.
