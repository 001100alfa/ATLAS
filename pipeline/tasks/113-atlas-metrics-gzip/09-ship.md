# Görev 113 — Teslim

`atlas-metrics.yml` `--group-by day --format prometheus --gzip` artifact.

## Uygulama

- Yeni step: `Generate group prometheus (gzip, SPEC 103/113)`.
  - `if: steps.metrics.outputs.has_data == 'true'`.
  - `atlas metrics --limit 100 --group-by day --format prometheus
    --out metrics-group-day.prom --gzip`.
  - `||` fallback (`echo "(...)" > metrics-group-day.prom.gz`).
- Upload artifact listesine `metrics-group-day.prom.gz` eklendi.
- Mevcut 4 artifact (SPEC 074+095) DOKUNULMADI (BİT-UYUMLU).

## Kanıt

- +4 test (`tests/test_github_workflows.py` SPEC 113 bölümü):
  - Cost step + `--group-by day` + `--format prometheus` + `--gzip` +
    doğru dosya adı.
  - Conditional `has_data=true` (fail-safe).
  - Upload artifact `metrics-group-day.prom.gz` içerir.
  - Mevcut 4 artifact yerinde.
- 1447 → **1451 yeşil** (+4), 12 skip. cov %91.40.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 074/084/095: mevcut artifact üretimi + PR comment AYNI.
- SPEC 103: `--gzip` semantiği AYNI (CLI'nin YAN etkisi).
