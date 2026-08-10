# Görev 185 — Teslim

`atlas-doctor.yml` webhook payload'a `strict` alanı
(SPEC 177 CLI kardeşi; workflow paritel).

## Uygulama
- SPEC 135 `Post doctor alert webhook` step payload heredoc'una
  **yeni alan** `"strict": true`.
- Değer: **sabit `true`** — workflow `atlas doctor --strict --scan-src`
  çalıştırıyor (SPEC 070); doğal olarak strict modda.
- Mevcut 6 alan (`alert`, `rc_strict`, `rc_diff`, `rc_hist`, `run_id`,
  `sha`) DOKUNULMADI.
- Step adı SPEC referansına `185` eklendi (kalıp).
- Payload açıklama comment'i güncellendi (SPEC 185 not).

## Kanıt
- +3 test (`tests/test_github_workflows.py` SPEC 185 bölümü):
  1. Payload heredoc'unda `"strict": true` var
  2. Mevcut 6 alan (SPEC 135) AYNI
  3. Step adı SPEC 185 referansı içerir
- Toplam workflow test 122 → **125 yeşil** (+3 SPEC 185).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 070 atlas doctor --strict --scan-src davranışı AYNI.
- SPEC 131/135 webhook step tetik koşulu (`if:` conditional) AYNI.
- SPEC 135 `continue-on-error: true` AYNI (webhook fail workflow durdurmaz).
- SPEC 135 `env.ALERT_WEBHOOK_URL: secrets.ATLAS_ALERT_WEBHOOK_URL` AYNI.
- SPEC 147 schema artifact step AYNI.
- SPEC 177 CLI payload strict alanı ile paritel (receiver CLI vs
  workflow ayırt etmesin — aynı alan, aynı anlam).

## Kalıp not (bu turdan)
Payload alan-ekleme (SPEC 032.4) hem CLI'da (SPEC 177) hem workflow'da
(SPEC 185) tutarlı olmalı — receiver aynı payload biçimini bekler.
Gelecek `alert-webhook` genişletmelerinde iki tarafı aynı turda
uygulamak "workflow-CLI parity" ilkesini bozmaz.
