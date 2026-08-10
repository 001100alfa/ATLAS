# Görev 160 — İhtiyaç

SPEC 147 (`atlas-doctor.yml` doctor-schema.prom.gz) ve SPEC 152
(`atlas-ci-status.yml` archive-schema.prom.gz) kalıbı. Şimdi
`atlas-metrics.yml` workflow'una `metrics --schema --format prometheus`
(SPEC 157) çıktısını artifact olarak eklemek gerek.

## Kabul

- `.github/workflows/atlas-metrics.yml` yeni step:
  `Generate metrics schema prometheus artifact (SPEC 160)`.
- `atlas metrics --schema --format prometheus > metrics-schema.prom`
  → shell `gzip -f metrics-schema.prom` → `metrics-schema.prom.gz`.
- `||` fallback (fail-safe SPEC 095/147/152 kalıbı).
- Conditional YOK (schema kısa devre — her zaman çalışır).
- Upload artifact listesine `metrics-schema.prom.gz` eklendi
  (mevcut atlas-metrics-report upload adımına eklenir; SPEC 147
  doctor kalıbı — ayrı upload adımı YOK).
- Mevcut atlas-metrics.yml davranışı BİT-UYUMLU (SPEC 023/043/074/084/103
  hepsi AYNI).
