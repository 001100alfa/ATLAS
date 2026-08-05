# Görev 095 — İhtiyaç

SPEC 074 `atlas-metrics.yml` üç artifact üretir (human, json, prometheus)
ama grup başına $ cost YOK. SPEC 084 `--group-by --with-cost`
eklendikten sonra PR/CI'de görünmesi gerek.

## Kabul

- `.github/workflows/atlas-metrics.yml` yeni step: `Generate cost by day`.
- `atlas metrics --group-by day --with-cost --json --limit 100` →
  `metrics-cost-by-day.json` artifact.
- Env fiyat CI'de yoksa cost 0 (SPEC 013 fail-safe); UYARI stderr'e
  gider workflow adımı kırmaz.
- Mevcut artifact 3'ü (`metrics-human.txt`, `metrics.json`,
  `metrics.prom`) DOKUNULMADI (BİT-UYUMLU).
- Yeni artifact upload listesine `metrics-cost-by-day.json` eklendi.
- README badge tablosu (SPEC 082 gate) etkilenmez — workflow sayısı AYNI.
