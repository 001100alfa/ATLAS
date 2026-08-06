# Görev 117 — İhtiyaç

SPEC 112 atlas-vault.yml restore + verify --strict step mevcut. Job
fail'de artifact atılıp workflow durur ama "hangi doctor sağlık
uyarısı" kaydı YOK. Restore edilen vault'a doctor gate ekle → tam
integrity.

## Kabul

- `.github/workflows/atlas-vault.yml` restore-verify step'inden SONRA:
  `atlas doctor --strict --scan-src` `/tmp/verify-vault` üzerinde
  ATLAS_VAULT env ile.
- Bulgu → workflow fail (rc != 0).
- has_vault=false ise atlar (fail-safe).
- Mevcut backup + restore + verify + upload step'leri DOKUNULMADI.
