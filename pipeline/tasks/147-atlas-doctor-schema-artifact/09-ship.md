# Görev 147 — Teslim

`.github/workflows/atlas-doctor.yml` schema prometheus gzip artifact.

## Uygulama
- Yeni step: `Generate schema prometheus artifact (SPEC 147)`.
- `atlas doctor --schema --format prometheus --out doctor-schema.prom --gzip`
  → `doctor-schema.prom.gz`.
- Conditional YOK (schema kısa devre).
- `||` fallback (fail-safe SPEC 095 kalıbı).
- Upload artifact listesine `doctor-schema.prom.gz` eklendi.
- Mevcut 4 artifact DOKUNULMADI (BİT-UYUMLU).

## Kanıt
- +4 test (`tests/test_github_workflows.py` SPEC 147 bölümü).
