# Görev 194 — Teslim

`ai-cli status --schema` JSON'a `alert_options` (1) + `alert_payload` (8).

## Uygulama
- SPEC 175/181/188/189/190 kalıbı ai-cli için.
- alert_payload 8 alan: 6 SPEC 170 + 2 SPEC 180 (size_bytes + timestamp).
- Prometheus'a EKLENMEDİ; 4 metric aile korunur.

## Kanıt
- +5 test; ai_cli_status_schema regresyon 27 yeşil.
