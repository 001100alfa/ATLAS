# Görev 181 — Teslim

`doctor --schema` JSON'a `alert_options` + `alert_payload` alanları
(SPEC 032.4 bit-uyumlu; SPEC 175 metrics kalıbı; SPEC 168/177 belgeleme).

## Uygulama
- `_doctor_schema_descriptor()` JSON'a 2 yeni alan:
  - `alert_options`: 1 CLI seçeneği (`--alert-webhook URL`, SPEC 168).
  - `alert_payload`: 4 alan (3 SPEC 168 + 1 SPEC 177) her biri
    `{name, type, when, spec, desc}`.
- Prometheus çıktısına EKLENMEDİ (SPEC 175 YAGNI kalıbı; mevcut 6
  metric aile sayısı korunur).
- notes: SPEC 168 + SPEC 177 + SPEC 181 satırları.
- Mevcut top_level/quality_fields/backend_options/retry_pricing_envs/
  storage_envs/exit_codes DOKUNULMADI.

## Kanıt
- +7 test (`tests/test_cli_doctor_schema_alert_webhook_doc.py`):
  1. `alert_options` alanı `--alert-webhook URL` (SPEC 168)
  2. `alert_payload` alanı 4 alan (alert/warnings/quality_warnings/strict)
  3. Spec referansları (168 3× + 177 1×)
  4. Her alan `when=always` (POST atılırsa hep yazılır)
  5. notes'a SPEC 168 + 177 + 181 satırları
  6. Prometheus çıktısı DOKUNULMADI (6 metric aile AYNI)
  7. SPEC 040 mevcut top_level/quality_fields/exit_codes bit-uyumlu
- doctor_schema regresyon 42 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 040 JSON şeması geriye uyumlu (SPEC 032.4 alan-ekleme).
- SPEC 128/134/142 Prometheus çıktısı AYNI (6 metric aile).
- SPEC 166 --format json-lines NDJSON DOKUNULMADI (yeni alanlar
  otomatik `top_level`/`quality_field`/`exit_code`/backend_option/env
  tipine düşmüyor — sonraki tur için: SPEC 166'ya `alert_option` +
  `alert_payload_field` tipleri eklemek YAGNI).
- SPEC 168 POST tetik ölçütü + SPEC 177 payload alanları AYNI.
