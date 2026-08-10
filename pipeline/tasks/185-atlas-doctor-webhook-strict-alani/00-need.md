# Görev 185 — İhtiyaç

SPEC 177 CLI `doctor --alert-webhook` payload'ına `strict` alanı
eklendi (SPEC 032.4 bit-uyumlu). SPEC 135 `atlas-doctor.yml` webhook
step'i CI'da doctor gate FAIL olduğunda payload gönderir ama `strict`
alanı YOK — receiver "workflow strict modda mı?" bilgisini payload'dan
göremez (CLI ile paritel değil).

## Kabul

- `.github/workflows/atlas-doctor.yml` `Post doctor alert webhook`
  step'inin payload heredoc'una **yeni alan** `strict` (bool):
  ```json
  {"alert":"doctor",
   "rc_strict":"...",
   "rc_diff":"...",
   "rc_hist":"...",
   "run_id":"...",
   "sha":"...",
   "strict": true}
  ```
- Değer: `true` (SPEC 070 workflow zaten `atlas doctor --strict
  --scan-src` çalıştırıyor — strict SABIT `true`; SPEC 032
  --strict davranışı işlemin doğası).
- Not olarak SPEC 177 kalıp referansı payload'a yansıtıldı.
- Mevcut 6 alan (`alert`, `rc_strict`, `rc_diff`, `rc_hist`,
  `run_id`, `sha`) DOKUNULMADI.
- Test: SPEC 135 mevcut testleri kırmaz + yeni test `strict:true`
  payload heredoc'unda geçtiğini doğrular.
- `if:` conditional + `continue-on-error: true` AYNI.
