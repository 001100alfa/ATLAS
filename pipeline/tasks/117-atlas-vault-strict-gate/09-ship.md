# Görev 117 — Teslim

`.github/workflows/atlas-vault.yml` doctor gate on restored vault.

## Uygulama
- Yeni step: `Doctor gate on restored vault (SPEC 117)`.
- ATLAS_VAULT=/tmp/verify-vault + `atlas doctor --strict --scan-src`.
- has_vault=true conditional (fail-safe).
- Mevcut backup + restore-verify + upload step'leri DOKUNULMADI.

## Kanıt
- +4 test; 1474 → **1478 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 041/101/102/112: mevcut akışlar AYNI.
