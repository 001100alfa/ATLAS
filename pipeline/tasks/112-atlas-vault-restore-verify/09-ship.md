# Görev 112 — Teslim

`.github/workflows/atlas-vault.yml` restore + verify integrity step.

## Uygulama

- Yeni step: `Restore + verify (integrity check, SPEC 112)`.
  - `set -e` + `ls archive/vault-*.tar.gz.001 | sort | tail -1`.
  - `atlas vault restore <first> --split --apply --vault-root /tmp/verify-vault`.
  - `atlas vault verify --vault-root /tmp/verify-vault --strict`.
  - Herhangi biri başarısız → workflow fail (exit ≠ 0).
- Step yalnız `has_vault=true` iken çalışır (fail-safe).
- Mevcut backup + upload step'leri DOKUNULMADI (BİT-UYUMLU).

## Kanıt

- +4 test (`tests/test_github_workflows.py` SPEC 112 bölümü):
  - `Restore + verify` step + doğru komutlar (restore/verify/strict).
  - Conditional `has_vault` fail-safe.
  - `set -e` fail-fast.
  - Mevcut backup + upload step'leri korundu.
- 1443 → **1447 yeşil** (+4), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 107: backup + upload akışı AYNI.
- SPEC 102/042: restore --split + verify --strict davranışları AYNI.
