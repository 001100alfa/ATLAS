# Görev 141 — İhtiyaç

SPEC 131/135 kalıbı: alert-webhook post. `atlas-ci-status.yml` drift
tespitinde issue açar ama Slack/Discord/Teams push YOK. Env-driven
webhook eklenmeli.

## Kabul

- `.github/workflows/atlas-ci-status.yml` yeni step: `Post ci-status
  alert webhook (SPEC 131/141)`.
- Env `ALERT_WEBHOOK_URL: ${{ secrets.ATLAS_ALERT_WEBHOOK_URL }}`.
- Conditional: `env != '' AND steps.check.outputs.rc != '0'`.
- Payload: `{alert:"ci-status", rc, run_id, sha, event}`.
- `continue-on-error: true` (webhook fail workflow durdurmaz).
- Fail step ve issue step DOKUNULMADI.
