# Görev 173 — İhtiyaç

SPEC 160 (`atlas-metrics.yml`) `metrics --schema --format prometheus`
shell gzip (`> file && gzip -f`) kullanıyor. SPEC 161 (`atlas-vault.yml`)
`vault backup --schema --format prometheus` de aynı shell gzip. SPEC 162
ve SPEC 163 native `--out --gzip` destek sağladı. Şimdi workflow'ları
native destek kullanacak şekilde taşı — shell gzip disiplin ihlali.

## Kabul

- `atlas-metrics.yml` `Generate metrics schema prometheus artifact`
  step'i:
  - **eski**: `metrics --schema --format prometheus > f.prom &&
    gzip -f f.prom`
  - **yeni**: `metrics --schema --format prometheus --out
    metrics-schema.prom --gzip` (SPEC 162 native).
- `atlas-vault.yml` `Generate vault backup schema prometheus artifact`
  step'i:
  - **eski**: `vault backup --schema --format prometheus > f.prom &&
    gzip -f f.prom`
  - **yeni**: `vault backup --schema --format prometheus --out
    vault-backup-schema.prom --gzip` (SPEC 163 native).
- `atlas-vault.yml` `vault verify schema` step'i AYNI (zaten native
  --out --gzip SPEC 145).
- `||` fallback her ikisi için KORUNUR (fail-safe SPEC 095/147 kalıbı).
- Upload artifact path DEĞİŞMEDİ (`metrics-schema.prom.gz`,
  `vault-backup-schema.prom.gz`).
- Test: SPEC 160/161 mevcut testlerini güncelle veya yeni test ekle —
  workflow adımı native `--out --gzip` içermeli, shell `gzip -f`
  BULUNMAMALI.
- atlas-ci-status.yml SPEC 152 archive shell gzip **bu turda YOK**
  (sonraki tur adayı).
