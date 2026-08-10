# Görev 174 — İhtiyaç

SPEC 152 (`atlas-ci-status.yml`) `archive --schema --format prometheus`
shell gzip (`> file && gzip -f`) kullanıyor. SPEC 155 native `--out
--gzip` desteği zaten mevcut. SPEC 173 (metrics + vault backup)
kalıbının kardeşi — son shell gzip'i de native'e taşı.

## Kabul

- `atlas-ci-status.yml` `Generate archive schema prometheus artifact`
  step'i:
  - **eski**: `archive --schema --format prometheus > archive-schema.prom &&
    gzip -f archive-schema.prom`
  - **yeni**: `archive --schema --format prometheus --out
    archive-schema.prom --gzip` (SPEC 155 native).
- `||` fallback KORUNUR (fail-safe SPEC 095/147/152 kalıbı).
- Upload artifact path DEĞİŞMEDİ (`archive-schema.prom.gz`,
  name=`atlas-ci-status-schema`).
- Diğer step'ler (drift-scan, Setup uv, Install ATLAS, Upload drift,
  Post ci-status alert webhook, Fail on drift) DOKUNULMADI.
- Test: mevcut SPEC 152 testlerini güncelle — shell `gzip -f` yerine
  native `--out --gzip` bekle. SPEC 173 test tersine dönmemeli:
  `test_173_atlas_ci_status_hala_shell_gzip_kullanir_todo` **yeniden
  yazılır** — artık native olduğunu belgele.
