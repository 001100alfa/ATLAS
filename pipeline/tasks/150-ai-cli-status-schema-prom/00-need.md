# Görev 150 — İhtiyaç

SPEC 146 `ai-cli status --schema` JSON şema tanımı basar. Grafana/
Prometheus scrape için info-metric ailesi gerek (SPEC 140 vault verify
schema kalıbı; SPEC 128 doctor schema kalıbı).

## Kabul

- `atlas ai-cli status --schema --format prometheus [--pretty]`.
- 4 info-metric ailesi (SPEC 140 kalıbı):
  - `atlas_ai_cli_status_schema_version{version}` = 1
  - `atlas_ai_cli_status_schema_top_level{name, type}` = 1
  - `atlas_ai_cli_status_schema_exit_code{code}` = 1
  - `atlas_ai_cli_status_schema_format{name, spec}` = 1
- HELP/TYPE her metric için (Prometheus text v0.0.4).
- Label escape (`\` `"` `\n`).
- `tools/ai-cli/` dizini gerekmez (SPEC 146 kısa devre AYNI).
- `--format prometheus` YOKSA SPEC 146 JSON AYNI.
- Semantik MUTEX: `--format prometheus` yalnız `--schema` ile birlikte
  → aksi SPEC HATASI exit 2.
- Normal `status <name>` davranışı BİT-UYUMLU (--format prometheus
  yalnız --schema modunda geçerli).
