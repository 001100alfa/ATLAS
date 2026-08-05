# Görev 112 — İhtiyaç

SPEC 107 `atlas-vault.yml` scheduled backup + split parçalarını üretir
ama parça birleştirme + restore + verify ile "sağlam mı" testi YOK.
Backup üretilip de restore edilemezse fark edilmez. Integrity check
gerek.

## Kabul

- `.github/workflows/atlas-vault.yml` yeni step:
  `Restore + verify (integrity check)`.
- Backup üretildikten sonra:
  1. `atlas vault restore <first.001> --split --apply --vault-root /tmp/verify-vault`
  2. `atlas vault verify --vault-root /tmp/verify-vault --strict`
- Herhangi biri başarısız → workflow FAIL (exit ≠ 0).
- Vault yoksa (SPEC 107 has_vault=false) → step atlanır (fail-safe).
- Mevcut backup + upload step'leri DOKUNULMADI (BİT-UYUMLU).
