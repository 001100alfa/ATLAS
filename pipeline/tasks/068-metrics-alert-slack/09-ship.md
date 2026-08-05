# Görev 068 — Teslim

`atlas metrics --alert-slack URL` — Slack `{text}` provider format.

## Uygulama

- `_cmd_metrics` alert dallanmasında SPEC 064'ün sonrasında ek `--alert-slack`
  branch: payload `{text: markdown-str}` üret, `_post_alert_webhook`
  ile POST.
- Markdown: `:warning:` emoji + `> {msg}` quote + records/tokens/cache_r
  code blocks.
- Parser: `--alert-slack URL` bayrak. Diğer alert kanalları ile ORTOGONAL.

## Kanıt

- +5 test (`tests/test_cli_metrics_alert_slack.py`):
  - Payload `{text}` format + Slack-only keys (no `alert`, `records`, ...).
  - 500 stderr uyarı + exit 8 KORUR.
  - Eşik aşılmadı → POST yok.
  - Slack + Webhook + Email üçü ortogonal (aynı çağrıda hepsi çalışır +
    payload'lar farklı format).
  - `--alert` yok → `--alert-slack` etkisiz.
- 1061 → **1066 yeşil**, 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 059 SMTP + SPEC 064 webhook BİT-UYUMLU.
- Exit 8 semantiği KORUR (Slack yan etkiden bağımsız).
- `_post_alert_webhook` public-ish (SSRF savunma + timeout aynı).
