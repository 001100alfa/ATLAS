# Görev 171 — İhtiyaç

SPEC 166 doctor `--schema --format json-lines` NDJSON kalıbı archive
için de gerek. SPEC 149 archive --schema JSON default; SPEC 164
sub_commands alanı; SPEC 151 --format prometheus. Şimdi NDJSON stream.

## Kabul

- `atlas archive --schema --format json-lines [--out PATH [--gzip]]`.
- NDJSON stream (SPEC 087/126/166 kalıbı):
  - Her top_level: `{"type":"top_level","name":...,"field_type":...,"desc":...}`
  - Her exit_code: `{"type":"exit_code","code":...,"desc":...}`
  - Her format: `{"type":"format","name":...,"spec":...,"desc":...}`
  - Her sub_command (SPEC 164): `{"type":"sub_command","name":...,
    "exit_codes":[...], "spec":..., "desc":...}`
  - Son satır: `{"type":"summary","schema_version":"1",
    "top_level_count":..., "exit_codes_count":..., "formats_count":...,
    "sub_commands_count":...}`
- Parser: `--format` choices'a `json-lines` eklendi.
- MUTEX: `--format json-lines` yalnız `--schema` ile (SPEC 151/166
  kalıbı; normal archive modda REDDEDİR — SPEC HATASI exit 2).
- `--out PATH [--gzip]` desteği (SPEC 155/166 kalıbı).
- Mevcut SPEC 149 JSON default + SPEC 151 Prometheus + SPEC 155 --out
  --gzip yolları DOKUNULMADI.
