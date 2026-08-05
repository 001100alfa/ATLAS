# Görev 113 — İhtiyaç

SPEC 095 `atlas-metrics.yml` `metrics-cost-by-day.json` düz JSON.
SPEC 103 `atlas metrics --group-by prometheus --out --gzip` mevcut ama
workflow'da kullanılmıyor. Grup Prometheus gzip artifact eklenmeli
(long-term storage boyut).

## Kabul

- `.github/workflows/atlas-metrics.yml` yeni step:
  `Generate group prometheus (gzip, SPEC 103/113)`.
- `atlas metrics --group-by day --format prometheus --out
  metrics-group-day.prom --gzip` → `metrics-group-day.prom.gz`.
- `has_data=true` conditional (SPEC 095 kalıbı).
- `|| echo` fallback (fail-safe).
- Upload artifact listesine `metrics-group-day.prom.gz` eklendi.
- Mevcut 4 artifact (`metrics-human.txt`, `metrics.json`,
  `metrics.prom`, `metrics-cost-by-day.json`) DOKUNULMADI.
