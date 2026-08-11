# Görev 202 — İhtiyaç

SPEC 170 ai-cli status --alert-webhook payload'ında `bin_path` yok.
SPEC 037.4 report'ta bin_path var; payload'a yansıt.

## Kabul
- CLI payload'a `bin_path: str|null`.
- SPEC 194 --schema alert_payload'a `bin_path` (spec=202).
- Mevcut alanlar DOKUNULMADI.
