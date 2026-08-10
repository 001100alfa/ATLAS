# Görev 160 — Teslim

`.github/workflows/atlas-metrics.yml` metrics schema prometheus gzip
artifact adımı (SPEC 147/152 kalıbı, SPEC 157 üstüne).

## Uygulama
- Yeni step: `Generate metrics schema prometheus artifact (SPEC 160)`.
- `uv run atlas metrics --schema --format prometheus > metrics-schema.prom
  && gzip -f metrics-schema.prom` (shell tabanlı; metrics --out --gzip
  henüz yok).
- `||` fallback (fail-safe SPEC 095/147/152 kalıbı).
- Conditional YOK schema step için — kısa devre her zaman çalışır.
- Upload artifact listesine `metrics-schema.prom.gz` eklendi (SPEC 147
  doctor kalıbı; ayrı upload adımı YOK — mevcut atlas-metrics-report
  listesinin sonuna eklendi).
- Mevcut 6 artifact DOKUNULMADI (BİT-UYUMLU).

## Kanıt
- +5 test (`tests/test_github_workflows.py` SPEC 160 bölümü):
  - schema step var + doğru komut/argümanlar
  - `||` fallback
  - upload artifact path içinde `metrics-schema.prom.gz`
  - Mevcut 6 artifact (metrics-human.txt, .json, .prom,
    metrics-cost-by-day.json, metrics-group-day.prom.gz,
    .atlas/alert-history.jsonl) LISTEDE AYNI
  - Schema step conditional YOK
- Toplam workflow test 95 → **100 yeşil** (+5).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 023/043/074/084/095/103/113/126 mevcut atlas-metrics.yml
  davranışı AYNI.
- Setup uv + Install ATLAS + mevcut steps DOKUNULMADI.
