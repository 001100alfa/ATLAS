# Görev 166 — İhtiyaç

SPEC 040 `doctor --schema` tek büyük JSON obje basar. SPEC 087
vault verify `--format json-lines` NDJSON stream (bulgu başına 1 satır +
summary) kalıbı doctor için de gerek — büyük şema (SPEC 142 sonrası 6+
metric ailesi + backend_options + retry_pricing_envs + storage_envs)
stream olarak daha kullanışlı.

## Kabul

- `atlas doctor --schema --format json-lines`.
- NDJSON stream (SPEC 087/126 kalıbı):
  - `{"type":"top_level","name":...,"type":...,"desc":...}` her alan başına
  - `{"type":"quality_field","name":...,"spec":...}` her alan başına
  - `{"type":"backend_option","name":...,"value":...}` (SPEC 142)
  - `{"type":"env","group":"retry_pricing","name":...}` (SPEC 142)
  - `{"type":"env","group":"storage","name":...}` (SPEC 142)
  - `{"type":"exit_code","code":...,"desc":...}` her kod başına
  - Son satır: `{"type":"summary","schema_version":"1",
     "top_level_count":..., "quality_fields_count":...,
     "exit_codes_count":..., "backend_options_count":...,
     "retry_pricing_envs_count":..., "storage_envs_count":...}`
- Parser: `--format` choices'a `json-lines` eklendi (mevcut human/
  prometheus'a).
- MUTEX: `--format json-lines` yalnız `--schema` ile birlikte kullanılır
  → normal doctor modunda REDDEDİR (SPEC HATASI exit 2, SPEC 158 kalıbı).
- `--out PATH [--gzip]` desteklenir (SPEC 145/155/156/162 kalıbı):
  parent auto-mkdir + auto-suffix .gz + gzip.open("wt"); IO hatası
  exit 2. Mevcut SPEC 134 `--schema --out yalnız --format prometheus`
  MUTEX genişletildi (`prometheus VEYA json-lines`).
- Mevcut SPEC 040 JSON default (--format yok) AYNI bit-uyumlu.
- Mevcut SPEC 128 Prometheus DOKUNULMADI.
