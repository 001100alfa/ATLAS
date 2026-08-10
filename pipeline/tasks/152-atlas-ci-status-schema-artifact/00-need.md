# Görev 152 — İhtiyaç

SPEC 147 kalıbı `atlas-doctor.yml` doctor schema prometheus gzip
artifact üretiyor. `atlas-ci-status.yml` için de aynı kalıp SPEC 151
`archive --schema --format prometheus` üstüne — Grafana/Prometheus
scrape için archive schema info-metric artifact.

## Kabul

- `.github/workflows/atlas-ci-status.yml` yeni step:
  `Generate archive schema prometheus artifact (SPEC 152)`.
- `atlas archive --schema --format prometheus > archive-schema.prom`
  → shell `gzip -f archive-schema.prom` → `archive-schema.prom.gz`.
  (SPEC 155 --out --gzip henüz yok; shell gzip yeterli).
- `||` fallback (fail-safe SPEC 095/147 kalıbı).
- Yeni upload step: `Upload atlas-ci-status schema artifact`
  (name=`atlas-ci-status-schema`, path=`archive-schema.prom.gz`,
  retention-days=30, `if: always()`).
- `Setup uv` + `Install ATLAS` adımları eklendi (mevcut Python
  setup DOKUNULMADI — `gen_ci_badges.py` için gerekli).
- Mevcut drift-scan davranışı BİT-UYUMLU (SPEC 089/125/141 hepsi AYNI).
- Conditional YOK (schema kısa devre — her zaman çalışır).
