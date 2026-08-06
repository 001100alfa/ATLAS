# Görev 135 — İhtiyaç

SPEC 131 atlas-metrics.yml alert-webhook POST'u ekledi. atlas-doctor.yml
tarafında da doctor gate FAIL (`rc_strict` / `rc_diff` / `rc_hist`
!= 0) durumunda benzer webhook ping gerek.

## Kabul

- `.github/workflows/atlas-doctor.yml` yeni step: `Post doctor alert webhook`.
- Env `ALERT_WEBHOOK_URL: ${{ secrets.ATLAS_ALERT_WEBHOOK_URL }}`.
- Conditional: `env != ''` AND (any rc != '0').
- POST payload: `{alert:"doctor", rc_strict, rc_diff, rc_hist, run_id, sha}`.
- `continue-on-error: true` (webhook fail workflow durdurmaz).
- Fail step'i ile ORTOGONAL — webhook step önce, sonra fail workflow.
