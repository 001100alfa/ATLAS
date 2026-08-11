# Görev 193 — İhtiyaç

`atlas-vault.yml` webhook step YOK. SPEC 135/141/185/191 kalıbı vault backup için.

## Kabul
- Backup step'e `id: backup` + `continue-on-error: true` + `rc=$?` output.
- Yeni step: `Post vault-backup alert webhook (SPEC 135/141/185/191/193)`.
- Env `ALERT_WEBHOOK_URL: secrets.ATLAS_ALERT_WEBHOOK_URL`.
- Payload: `alert=vault-backup` + rc + run_id + sha + timestamp (SPEC 191).
- Conditional: env + rc != 0 + rc != ''.
- `continue-on-error: true`.
- Mevcut restore-verify + doctor gate + upload adımları AYNI (rc-condition eklenmeli
  ki backup fail olursa devam etmesinler — ayrı kapsam, bu turda değil).
