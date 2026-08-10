# Görev 161 — Teslim

`.github/workflows/atlas-vault.yml` vault verify + backup schema
prometheus gzip artifact adımları (SPEC 147/152/160 kalıbı).

## Uygulama
- Yeni step 1: `Generate vault verify schema prometheus artifact (SPEC 161)`
  `atlas vault verify --schema --format prometheus --out
   vault-verify-schema.prom --gzip` (SPEC 145 mevcut CLI komutu).
- Yeni step 2: `Generate vault backup schema prometheus artifact (SPEC 161)`
  `atlas vault backup --schema --format prometheus >
   vault-backup-schema.prom && gzip -f vault-backup-schema.prom`
  (SPEC 158 yeni; --out --gzip henüz yok — shell tabanlı).
- `||` fallback her ikisi için (fail-safe SPEC 095/147 kalıbı).
- Conditional YOK schema step'leri için — kısa devre her zaman çalışır
  (has_vault check'e bağlı değil).
- Yeni upload step: `Upload atlas-vault schema artifacts (SPEC 161)`
  (name=`atlas-vault-schema`, path her iki .gz, `if: always()`,
  `if-no-files-found: ignore`).
- Mevcut `vault-backup-parts` upload adı + conditional AYNI.

## Kanıt
- +7 test (`tests/test_github_workflows.py` SPEC 161 bölümü):
  - vault verify schema step + doğru komut/argümanlar (--gzip dahil)
  - vault backup schema step + gzip komutu
  - Her iki step için `||` fallback
  - Her iki step conditional YOK
  - Upload step name=`atlas-vault-schema` + iki path
  - Upload `if: always()`
  - Mevcut vault-backup-parts upload conditional AYNI
- Toplam workflow test 100 → **107 yeşil** (+7).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 107/041/101/102/112/117/124 mevcut atlas-vault.yml davranışı AYNI.
- Setup uv + Install ATLAS + mevcut backup adımları DOKUNULMADI.
- vault-backup-parts upload adı, conditional, path AYNI.
