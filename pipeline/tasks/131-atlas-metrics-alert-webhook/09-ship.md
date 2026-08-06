# Görev 131 — Teslim

`atlas-metrics.yml` alert-webhook post step.

## Uygulama
- Yeni step: `Post alert webhook (SPEC 064/131)`.
- Env `ALERT_WEBHOOK_URL: ${{ secrets.ATLAS_ALERT_WEBHOOK_URL }}`.
- `atlas metrics --alert 30 --alert-webhook "$ALERT_WEBHOOK_URL"`.
- Conditional: `has_data + env != ''` (SPEC 095 fail-safe).
- `continue-on-error: true` — webhook fail job kırmaz.
- Mevcut step'ler DOKUNULMADI.

## Kanıt
- +4 test; 1512 → **1516 yeşil**.
