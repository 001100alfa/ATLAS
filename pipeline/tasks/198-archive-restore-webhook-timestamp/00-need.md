# Görev 198 — İhtiyaç

SPEC 176 archive --restore --alert-webhook payload'ında `timestamp` yok.
SPEC 180/186/187/191/192 kardeşi.

## Kabul
- CLI payload'a `timestamp: ISO 8601` (SPEC 032.4).
- SPEC 189 archive --schema alert_payload'a `timestamp` (spec=198).
- SPEC 182 archive --restore --schema alert_payload_fields'e `timestamp` (spec=198).
- Mevcut alanlar DOKUNULMADI.
