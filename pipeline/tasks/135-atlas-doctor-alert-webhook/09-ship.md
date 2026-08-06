# Görev 135 — Teslim

`.github/workflows/atlas-doctor.yml` alert-webhook gate.

## Uygulama
- Yeni step: `Post doctor alert webhook (SPEC 131/135)`.
- Env `ALERT_WEBHOOK_URL: ${{ secrets.ATLAS_ALERT_WEBHOOK_URL }}`.
- Conditional: env != '' AND (rc_strict|rc_diff|rc_hist != '0').
- Payload: `{alert:"doctor", rc_*, run_id, sha}`.
- `continue-on-error: true` — webhook fail workflow durdurmaz.
- Fail step'inden ÖNCE çalışır (ORTOGONAL sıra).

## Kanıt
- +4 test; +4 → **1563 yeşil**.
