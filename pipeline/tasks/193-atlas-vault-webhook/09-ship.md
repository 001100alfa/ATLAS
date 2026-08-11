# Görev 193 — Teslim

`atlas-vault.yml` yeni webhook step (SPEC 178 CLI kardeşi).

## Uygulama
- Backup step id=backup + continue-on-error + `rc=$?` output.
- Yeni step: `Post vault-backup alert webhook (SPEC 135/141/185/191/193)`.
- Payload: `alert=vault-backup` + rc + run_id + sha + timestamp.
- Conditional: env + rc != 0.
- `continue-on-error: true`.

## Kanıt
- +4 test SPEC 193; workflow test 132 yeşil.
