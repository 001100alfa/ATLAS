# Görev 124 — Teslim

`.github/workflows/atlas-vault.yml` retention verify step.

## Uygulama
- Yeni step: `Verify retention (--keep 7, SPEC 041.1/124)`.
- `find archive/ -name 'vault-*.tar.gz.*' | wc -l` sayı kontrolü.
- Ana `.tar.gz` split sonrası silinmiş olmalı (0 beklenir).
- 0 parça → `::error::` + exit 1.

## Kanıt
- +3 test; 1497 → **1500 yeşil**, ruff temiz.
