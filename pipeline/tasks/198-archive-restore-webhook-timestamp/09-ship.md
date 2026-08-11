# Görev 198 — Teslim

archive --restore webhook payload + iki schema `timestamp` alan-ekleme.

## Uygulama
- SPEC 176 CLI payload'a 7. alan `timestamp`.
- SPEC 189 archive --schema alert_payload'a `timestamp` (spec=198).
- SPEC 182 archive --restore --schema alert_payload_fields'e `timestamp` (spec=198).
- SPEC 182/189 mevcut testleri 6→7 alan güncellendi.

## Kanıt
- +4 test; archive regresyon 94 yeşil.
