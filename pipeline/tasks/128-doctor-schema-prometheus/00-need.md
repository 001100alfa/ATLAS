# Görev 128 — İhtiyaç

SPEC 040 `atlas doctor --schema` yalnız JSON basar. Grafana/Prometheus
scrape için `atlas_doctor_schema_info{version, field, type} 1` info
metric ailesi gerek — statik bilgiyi Prometheus'a gauge olarak
yayımlar (Prometheus info-metric kalıbı).

## Kabul

- `atlas doctor --schema --format prometheus`.
- Prometheus text v0.0.4 çıktı, 3 metric ailesi:
  - `atlas_doctor_schema_version{version}` = 1 (info)
  - `atlas_doctor_schema_top_level_field{name, type}` = 1 (info; her
    top_level alan için)
  - `atlas_doctor_schema_quality_field{name, spec}` = 1 (info; her
    quality alan için)
  - `atlas_doctor_schema_exit_code{code}` = 1 (info; her exit code)
- HELP/TYPE her metric için (v0.0.4).
- Label escape (`\` `"` newline).
- `--format json`/`--format` yoksa SPEC 040 JSON çıktı AYNI (BİT-UYUMLU).
