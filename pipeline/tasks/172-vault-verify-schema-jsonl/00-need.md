# Görev 172 — İhtiyaç

SPEC 166 doctor `--schema --format json-lines` ve SPEC 171 archive
`--schema --format json-lines` NDJSON kalıbı vault verify için de gerek.
SPEC 136 vault verify --schema (JSON default); SPEC 140 --format
prometheus; SPEC 145 --out --gzip.

**Önemli:** vault verify'nin `--format json-lines` **normal modda ZATEN
VAR** (SPEC 087 — bulgu başına 1 satır + summary). Yeni SPEC 172
`--schema --format json-lines` **şema için AYRI dal** — bulgular yerine
şema alanlarını NDJSON streamler.

## Kabul

- `atlas vault verify --schema --format json-lines [--out PATH [--gzip]]`.
- NDJSON stream (SPEC 087/126/166/171 kalıbı):
  - Her top_level: `{"type":"top_level","name":...,"field_type":...,"desc":...}`
  - Her exit_code: `{"type":"exit_code","code":...,"desc":...}`
  - Her format: `{"type":"format","name":...,"spec":...,"desc":...}`
  - Son satır: `{"type":"summary","schema_version":"1",
    "top_level_count":..., "exit_codes_count":..., "formats_count":...}`
- SPEC 087 normal `vault verify --format json-lines` (bulgu NDJSON)
  DOKUNULMADI — --schema flag'i dal ayırır.
- `--out PATH [--gzip]` desteği (SPEC 145/155/166 kalıbı).
- Parser DEĞİŞMEZ — `--format` choices'da `json-lines` mevcut (SPEC 087).
- Mevcut SPEC 136 JSON + SPEC 140 Prometheus + SPEC 145 --out --gzip
  dalları AYNI.
