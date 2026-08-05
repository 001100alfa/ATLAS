# Görev 064 — İhtiyaç

SPEC 059 SMTP alert atıyor. Ama modern operasyonel işlerde Slack/Discord/
Teams incoming webhook'ları daha yaygın. Cron/scheduled context'te email
gecikmeli, webhook anlık.

## Kabul

- `atlas metrics --alert-webhook URL` — `--alert` eşiği aşıldığında JSON POST.
- Payload: `{alert, hit_ratio_pct, threshold_pct, records, tokens_*, cache_*, message}`.
- Content-Type: `application/json; charset=utf-8`; UA: `atlas-alert-webhook/1.0`.
- Timeout 5s. Non-2xx / URLError / OSError / TimeoutError → False + err (exit 8 KORUR).
- Scheme yalnız http/https (SSRF savunma: file://, ftp:// reddedilir).
- `--alert-email` ile ORTOGONAL — ikisi verilirse ikisi de çalışır.
- `--alert` yoksa `--alert-webhook` etkisiz.

## Risk

- Payload provider-agnostic (Slack "text" field bekleyebilir ama incoming
  webhook custom JSON kabul eder). Provider-özel format için wrapper
  YAGNI — kullanıcı istiyorsa proxy yazar.
