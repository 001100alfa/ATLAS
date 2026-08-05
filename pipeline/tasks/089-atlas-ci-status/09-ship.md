# Görev 089 — Teslim

`.github/workflows/atlas-ci-status.yml` (scheduled daily + workflow_dispatch).

## Uygulama

- `on.schedule: - cron: "0 6 * * *"` — her gün 06:00 UTC (Istanbul 09:00).
- `on.workflow_dispatch: {}` — manuel tetik.
- `permissions: {contents: read, issues: write}`.
- Job `drift-scan`: `python tools/scripts/gen_ci_badges.py --check`
  → drift varsa `peter-evans/create-issue-from-file@v5` ile issue aç
  → `Fail on drift` (exit 1).
- README badge tablosu regen (SPEC 082 gate) — `atlas-ci-status` satırı
  alfabetik başa eklendi.

## Kanıt

- +7 test (`tests/test_github_workflows.py`, SPEC 089 bölümü):
  - YAML valid + name.
  - schedule cron `0 6 * * *`.
  - workflow_dispatch var.
  - permissions issues:write + contents:read.
  - gen_ci_badges.py --check çağrılıyor.
  - drift → create-issue-from-file conditional.
  - README badge satırı var.
- 1237 → **1244 yeşil** (+7), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 082 `ci-status.yml` push/PR gate DOKUNULMADI (SPEC 089 AYRI
  workflow).
- `gen_ci_badges.py` DOKUNULMADI (mevcut script kullanıldı).
