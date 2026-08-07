# Görev 140 — İhtiyaç

SPEC 136 `vault verify --schema` JSON şema tanımı basar. Grafana/
Prometheus scrape için info-metric ailesi gerek (SPEC 128 doctor
schema kalıbı).

## Kabul

- `atlas vault verify --schema --format prometheus`.
- 4 info-metric ailesi (SPEC 128 kalıbı):
  - `atlas_vault_verify_schema_version{version}` = 1
  - `atlas_vault_verify_schema_top_level{name, type}` = 1
  - `atlas_vault_verify_schema_exit_code{code}` = 1
  - `atlas_vault_verify_schema_format{name, spec}` = 1
- HELP/TYPE her metric için (Prometheus text v0.0.4).
- Label escape (`\` `"` `\n`).
- Vault dizini gerekmez (SPEC 136 kısa devre AYNI).
- `--format prometheus` YOKSA SPEC 136 JSON AYNI.
- Diğer `--strict/--out/--gzip` --schema modunda YOK sayılır (mevcut).
