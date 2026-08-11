# Görev 195 — İhtiyaç

SPEC 175 metrics --schema alert_payload listesine SPEC 187 `timestamp`
alan ekleme (belge güncellemesi).

## Kabul
- alert_payload sonuna `{name: timestamp, type: ISO 8601, when: webhook only, spec: 187}`.
- notes'a SPEC 187 + SPEC 195 satırları.
- Mevcut alanlar DOKUNULMADI.
