# Görev 151 — İhtiyaç

SPEC 149 `archive --schema` JSON şema tanımı basar. Grafana/Prometheus
scrape için info-metric ailesi gerek (SPEC 140/150 kalıbı).

## Kabul

- `atlas archive --schema --format prometheus [--pretty]`.
- 4 info-metric ailesi (SPEC 140 kalıbı):
  - `atlas_archive_schema_version{version}` = 1
  - `atlas_archive_schema_top_level{name, type}` = 1
  - `atlas_archive_schema_exit_code{code}` = 1
  - `atlas_archive_schema_format{name, spec}` = 1
- HELP/TYPE her metric için (Prometheus text v0.0.4).
- Label escape (`\` `"` `\n`).
- Arşiv kökü gerekmez (SPEC 149 kısa devre AYNI).
- `--format prometheus` YOKSA SPEC 149 JSON AYNI.
- Semantik MUTEX: `--format prometheus` yalnız `--schema` ile birlikte
  → aksi SPEC HATASI exit 2.
- Normal archive komutları (SPEC 007/012/033/065/071/075) BİT-UYUMLU.
