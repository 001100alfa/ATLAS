# Görev 131 — İhtiyaç

SPEC 064 `atlas metrics --alert-webhook URL` mevcut ama workflow'da
kullanılmıyor. Cache-hit oranı düşükse GitHub secret'tan gelen webhook
URL'ye POST atmak gerek. Env-driven: secret yoksa step atlanır (fail-
safe, SPEC 095 kalıbı).

## Kabul

- `.github/workflows/atlas-metrics.yml` yeni step: `Post alert webhook`.
- Env: `ALERT_WEBHOOK_URL: ${{ secrets.ATLAS_ALERT_WEBHOOK_URL }}`.
- Env boşsa step atlar (conditional `env.ALERT_WEBHOOK_URL != ''`).
- `atlas metrics --alert 30 --alert-webhook "$ALERT_WEBHOOK_URL"` —
  eşik %30 (SPEC 029 range 0-100).
- `has_data=true` conditional; `continue-on-error: true` (webhook
  başarısız olursa job kırılmasın — post best-effort).
- Mevcut step'ler DOKUNULMADI.
