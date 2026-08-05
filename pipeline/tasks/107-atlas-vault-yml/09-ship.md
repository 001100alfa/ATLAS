# Görev 107 — Teslim

`.github/workflows/atlas-vault.yml` scheduled backup + split.

## Uygulama

- Yeni workflow `.github/workflows/atlas-vault.yml`:
  - `on.schedule: cron: "0 3 * * *"` — her gün 03:00 UTC.
  - `on.workflow_dispatch: {}` — manuel tetik.
  - `permissions: contents: read`.
  - Job `backup`:
    - `Check vault exists` step → `has_vault` output.
    - `atlas vault backup --auto --split 50 --keep 7` (if has_vault).
    - Upload artifact `vault-backup-parts` (30 gün retention).
- README badge tablosu regen (SPEC 082 gate) — `atlas-vault` satırı
  alfabetik başa eklendi.

## Kanıt

- +8 test (`tests/test_github_workflows.py` SPEC 107 bölümü):
  - YAML valid + name.
  - schedule cron `0 3 * * *`.
  - workflow_dispatch var.
  - permissions contents:read.
  - `atlas vault backup --auto --split 50 --keep 7` çağrılıyor.
  - `vault/` yoksa skip (has_vault=false).
  - Upload artifact conditional + `vault-*.tar.gz.*` glob.
  - README badge satırı `atlas-vault` içerir.
- 1407 → **1415 yeşil** (+8), 12 skip.
- cov %91.37, mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 041/101: mevcut backup + split davranışları AYNI.
- SPEC 056/070/074: diğer workflow'lar DOKUNULMADI.
- SPEC 082: `gen_ci_badges.py` regen ile README güncellendi.
