# Görev 147 — İhtiyaç

SPEC 128/134 doctor `--schema --format prometheus --out --gzip` info-metric
artifact. CI/Grafana file_sd için atlas-doctor.yml workflow'una eklenmeli.

## Kabul

- `.github/workflows/atlas-doctor.yml` yeni step: `Generate schema
  prometheus artifact (SPEC 147)`.
- `atlas doctor --schema --format prometheus --out doctor-schema.prom
  --gzip` → `doctor-schema.prom.gz`.
- Schema kısa devre → conditional YOK (her zaman çalışır).
- `|| echo` fallback (SPEC 095 kalıbı).
- Upload artifact listesine `doctor-schema.prom.gz` eklendi.
- Mevcut 4 artifact (report/diff/history-all/history-strict) DOKUNULMADI.
