# Görev 068 — İhtiyaç

SPEC 064 `--alert-webhook` generic JSON POST. Slack incoming webhook
`{text}` bekler (ham JSON'u kabul eder ama düz string olarak render eder).
Kullanıcı SPEC 064 kullanınca Slack'te bozuk mesaj görüyor. Slack özel
wrapper gerek.

## Kabul

- `atlas metrics --alert-slack URL` — Slack incoming webhook için özel format.
- Payload: `{text: "..."}` — Slack'in bildiği format (markdown-benzeri
  `:warning:`, `> quote`, `` `code` ``).
- `--alert-webhook` + `--alert-email` + `--alert-slack` üçü ORTOGONAL
  (aynı çağrıda ikisi/üçü verilebilir).
- Exit 8 KORUR (SPEC 059 kalıbı).
- Alt-katman: `_post_alert_webhook` yeniden kullanılır (aynı SSRF savunma).

## Risk

- Slack `attachments`/`blocks` daha zengin ama YAGNI — `text` ile MVP.
  Kullanıcı zengin format için kendi wrapper'ını yazsın.
