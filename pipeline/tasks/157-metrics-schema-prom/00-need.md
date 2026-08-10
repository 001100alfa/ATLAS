# Görev 157 — İhtiyaç

SPEC 153 `metrics --schema` JSON şema tanımı basar. Grafana/Prometheus
scrape için info-metric ailesi gerek (SPEC 140/150/151 kalıbı).

## Kabul

- `atlas metrics --schema --format prometheus [--pretty]`.
- 4 info-metric ailesi (SPEC 140 kalıbı):
  - `atlas_metrics_schema_version{version}` = 1
  - `atlas_metrics_schema_top_level{name, type}` = 1
  - `atlas_metrics_schema_exit_code{code}` = 1
  - `atlas_metrics_schema_format{name, spec}` = 1
- HELP/TYPE her metric için (Prometheus text v0.0.4).
- Label escape (`\` `"` `\n`).
- metrics.jsonl gerekmez (SPEC 153 kısa devre AYNI).
- `--format prometheus` YOKSA SPEC 153 JSON AYNI.
- --schema kısa devre, mevcut `--format prometheus` (SPEC 043) davranışı
  yalnız --schema olmayan modda etkin.
