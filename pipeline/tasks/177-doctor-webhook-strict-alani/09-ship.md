# Görev 177 — Teslim

`doctor --alert-webhook` payload'a `strict` alanı (SPEC 032.4 bit-uyumlu).

## Uygulama
- SPEC 168 `doc_payload` dict'ine 4. anahtar `strict`:
  `bool(getattr(args, "strict", False))`.
- Mevcut 3 alan (`alert`, `warnings`, `quality_warnings`) DOKUNULMADI.
- Değer POST'tan önce hesaplanır; SPEC 032 exit 9 davranışı AYNI
  (payload'a yansıtır — davranışı değiştirmez).

## Kanıt
- +4 test (`tests/test_cli_doctor_alert_webhook_strict_field.py`):
  1. --strict verilmezse payload.strict = False
  2. --strict verilirse payload.strict = True + exit 9
  3. Mevcut alanlar AYNI + alan sayısı tam 4
  4. Bulgu yoksa POST atılmaz (bit-uyumlu; strict alanı da yok)
- doctor + alert_webhook regresyon 15 test yeşil (SPEC 168 + SPEC 177).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 032 --strict exit 9 semantiği AYNI (webhook ortogonal).
- SPEC 168 POST tetik ölçütü AYNI (`_has_quality_warning` True).
- SPEC 168 mevcut 3 payload alanı AYNI (bit-uyumlu ekleme).
- SPEC 064 `_post_alert_webhook()` implementasyonu AYNI.
- SPEC 021 normal doctor davranışı AYNI (--alert-webhook yoksa).
