# Görev 202 — Teslim

ai-cli status --alert-webhook payload + schema `bin_path` alan-ekleme.

## Uygulama
- SPEC 170 CLI payload'a 9. alan `bin_path: str|null`.
- SPEC 194 --schema alert_payload'a `bin_path` (spec=202).
- SPEC 180/194 testleri 8→9 alan güncellendi.

## Kanıt
- +3 test; ai_cli_status regresyon 60 yeşil (izole run).
