# Görev 161 — İhtiyaç

SPEC 147 (`atlas-doctor.yml` doctor-schema.prom.gz) + SPEC 152
(`atlas-ci-status.yml` archive-schema.prom.gz) + SPEC 160
(`atlas-metrics.yml` metrics-schema.prom.gz) kalıbı. Şimdi
`atlas-vault.yml` workflow'una vault verify + vault backup schema
artifact ekle.

## Kabul

- `.github/workflows/atlas-vault.yml` iki yeni schema adımı:
  1. `Generate vault verify schema prometheus artifact (SPEC 161)`:
     `atlas vault verify --schema --format prometheus --out
      vault-verify-schema.prom --gzip` (SPEC 145 mevcut CLI).
  2. `Generate vault backup schema prometheus artifact (SPEC 161)`:
     `atlas vault backup --schema --format prometheus >
      vault-backup-schema.prom && gzip -f vault-backup-schema.prom`
     (SPEC 158 yeni CLI; --out --gzip henüz yok — shell tabanlı).
- `||` fallback her ikisi için (fail-safe SPEC 095/147 kalıbı).
- Conditional YOK schema step'leri için — kısa devre her zaman çalışır
  (has_vault check'e bağlı değil).
- Yeni upload step: `Upload atlas-vault schema artifacts (SPEC 161)`
  (name=`atlas-vault-schema`, path=her iki .gz, `if: always()`,
  `if-no-files-found: ignore`).
- Mevcut `vault-backup-parts` upload adımı DOKUNULMADI (conditional AYNI).
- SPEC 107/041/101/102/112/117/124 mevcut atlas-vault.yml davranışı
  BİT-UYUMLU.
