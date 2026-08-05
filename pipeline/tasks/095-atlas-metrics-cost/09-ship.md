# Görev 095 — Teslim

`.github/workflows/atlas-metrics.yml` `--with-cost` entegrasyonu.

## Uygulama

- Yeni step: `Generate cost by day (SPEC 084/095)`.
  - `if: steps.metrics.outputs.has_data == 'true'`.
  - `uv run atlas metrics --limit 100 --group-by day --with-cost --json
    > metrics-cost-by-day.json`.
  - Env fiyat yoksa cost 0 (SPEC 013 fail-safe); komut kırılırsa `||`
    ile boş `{"unit":"day","groups":[]}` fallback (workflow durmaz).
- Upload artifact listesine `metrics-cost-by-day.json` eklendi.
- Mevcut 3 artifact (`metrics-human.txt`, `metrics.json`, `metrics.prom`)
  DOKUNULMADI (BİT-UYUMLU).

## Kanıt

- +4 test (`tests/test_github_workflows.py` SPEC 095 bölümü):
  - Cost step var + `--group-by day` + `--with-cost` + doğru dosya adı.
  - Step conditional `has_data=true` fail-safe.
  - Upload artifact listesi `metrics-cost-by-day.json` içerir.
  - Mevcut 3 artifact üye YEDI (BİT-UYUMLU).
- 1298 → **1302 yeşil** (+4), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 074: mevcut 3 artifact üretimi ve PR comment step'i AYNI.
- SPEC 082: `atlas-metrics.yml` workflow SAYISI değişmedi → README
  badge tablosu drift YOK.
