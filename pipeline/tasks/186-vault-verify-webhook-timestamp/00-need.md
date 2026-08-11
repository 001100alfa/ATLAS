# Görev 186 — İhtiyaç

SPEC 165 `vault verify --alert-webhook` payload'ında `timestamp` yok.
SPEC 180 ai-cli status kardeşi.

## Kabul
- Payload'a `timestamp: str (ISO 8601 seconds)` alan-ekleme
  (SPEC 032.4 bit-uyumlu).
- Mevcut 8 alan DOKUNULMADI.
- Değer: `datetime.now().isoformat(timespec="seconds")`.
