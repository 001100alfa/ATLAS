# Görev 186 — Teslim

`vault verify --alert-webhook` payload'a `timestamp` (SPEC 032.4).

## Uygulama
- SPEC 165 `vv_payload` dict'ine 9. anahtar `timestamp`:
  `datetime.now().isoformat(timespec="seconds")`.
- Mevcut 8 alan DOKUNULMADI.

## Kanıt
- +2 test (`tests/test_cli_vault_verify_webhook_timestamp.py`):
  ISO 8601 regex + alan sayısı 9.
- vault_verify regresyon 99 test yeşil.
- mypy + ruff temiz.

## Değişmeyen
- SPEC 165 POST tetik ölçütü AYNI.
- SPEC 042/087/136/140/145/172 AYNI.
