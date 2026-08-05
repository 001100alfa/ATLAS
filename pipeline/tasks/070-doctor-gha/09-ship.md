# Görev 070 — Teslim

`.github/workflows/atlas-doctor.yml` — doctor CI gate (SPEC 056 kardeşi).

## Uygulama

- `.github/workflows/atlas-doctor.yml`:
  - `on: push[main]` + `pull_request` + src/DECISIONS.md/baseline/YAML
    path filtresi.
  - permissions `pull-requests:write` + concurrency cancel-in-progress.
  - Job `doctor` (ubuntu-latest, timeout 5dk):
    - checkout → setup-uv → `uv sync --frozen --extra dev`.
    - `atlas doctor --strict --scan-src --json > doctor-report.json` (rc → OUTPUT).
    - Baseline varsa `--auto-baseline` (SPEC 062) delta (rc → OUTPUT); yoksa
      bilgi mesajı.
    - artifact upload (JSON + diff, 30 gün).
    - PR comment fail'de.
    - Fail step: `rc_strict OR rc_diff ≠ '0'` → exit 1.

## Kanıt

- +6 test (`tests/test_github_workflows.py::test_070_*`):
  - YAML valid + name.
  - Tetikleyiciler + src path filtresi.
  - Permissions + concurrency.
  - Step zinciri (checkout, setup-uv, upload-artifact, peter-evans,
    ATLAS komut, --auto-baseline dallanma).
  - `doctor` step continue-on-error + GITHUB_OUTPUT.
  - Fail step iki kaynak (rc_strict OR rc_diff).
- 1066 → **1072 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 056 vault-health.yml BİT-UYUMLU.
- SPEC 032 doctor + SPEC 062 auto-baseline BİT-UYUMLU.
- Kod tarafında değişiklik YOK — sadece deployment artefaktı.
