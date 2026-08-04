# Görev 056 — Teslim

`.github/workflows/vault-health.yml` — vault graf sağlığı CI gate'i.

## Uygulama

- **`.github/workflows/vault-health.yml`** (kod değil, deployment):
  - `on: push[main]` + `pull_request` + vault/src path filtresi
  - `permissions: contents:read, pull-requests:write`
  - `concurrency: cancel-in-progress: true`
  - 7 step: checkout → setup-uv → uv sync → verify (continue-on-error
    + rc → $GITHUB_OUTPUT) → upload-artifact (health.md) → comment PR
    (fail-only) → fail step (rc != 0 → exit 1).

## Kanıtlar

- +9 test (`tests/test_github_workflows.py`, PyYAML olmadığında skip):
  - YAML valid parse
  - Tetikleyiciler (push:main + pull_request) + vault path filtresi
    (PyYAML'ın `on:` → boolean `True` parse'ına karşı defensive)
  - `permissions: pull-requests:write`
  - `concurrency` grup + iptal
  - `verify` job (ubuntu-latest + timeout)
  - Step zinciri: checkout + setup-uv + peter-evans + upload-artifact
    + `atlas vault verify --strict --dump-report health.md`
  - PR comment step `pull_request` + `verify.outputs.rc != '0'` gate'li
  - Fail step son + `exit 1`
  - Verify step `continue-on-error: true` + `$GITHUB_OUTPUT`
- 912 → **921 yeşil**, 12 skip, cov %91.18 (kod eklenmedi).
- `uv run mypy src` temiz.
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Kullanıcı GitHub'a push ettiğinde vault-health workflow tetikleniyor.
- PR fail: workflow rapor artifact + PR comment.

## Değişmeyen sözleşme

- `atlas vault verify` (SPEC 042) BİT-UYUMLU.
- `--dump-report` (SPEC 052) BİT-UYUMLU.
- Pre-commit hook (SPEC 045/052) BİT-UYUMLU — workflow paralel gate.
- Kod tarafında hiçbir değişiklik YOK.
