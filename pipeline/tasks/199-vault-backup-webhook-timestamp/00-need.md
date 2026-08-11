# Görev 199 — İhtiyaç

SPEC 178 vault backup --alert-webhook payload'ına `timestamp` yok.
SPEC 190 --schema alert_payload'a paritel ekleme.

## Kabul
- CLI payload'a `timestamp: ISO 8601` (SPEC 032.4).
- SPEC 190 --schema alert_payload'a `timestamp` (spec=199).
