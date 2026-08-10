# Görev 158 — İhtiyaç

SPEC 154 `vault backup --schema` JSON şema tanımı basar. Grafana/
Prometheus scrape için info-metric ailesi gerek (SPEC 140/150/151/157
kalıbı).

## Kabul

- `atlas vault backup --schema --format prometheus [--pretty]`.
- 4 info-metric ailesi (SPEC 140 kalıbı):
  - `atlas_vault_backup_schema_version{version}` = 1
  - `atlas_vault_backup_schema_top_level{name, type}` = 1
  - `atlas_vault_backup_schema_exit_code{code}` = 1
  - `atlas_vault_backup_schema_format{name, spec}` = 1
- HELP/TYPE her metric için (Prometheus text v0.0.4).
- Label escape (`\` `"` `\n`).
- Vault dizini gerekmez (SPEC 154 kısa devre AYNI).
- `--format prometheus` YOKSA SPEC 154 JSON AYNI.
- Semantik MUTEX: `--format prometheus` yalnız `--schema` ile birlikte
  → aksi SPEC HATASI exit 2 (normal backup modda --format YOK).
- Parser: `--format` choices=["prometheus"] yeni argüman.
