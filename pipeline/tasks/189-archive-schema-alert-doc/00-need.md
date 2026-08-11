# Görev 189 — İhtiyaç

SPEC 175/181/188 kalıbı archive genel şeması için: SPEC 176 --restore
--alert-webhook belgele (SPEC 182 alert_payload_fields ile paritel).

## Kabul
- SPEC 149 archive_schema JSON'a `alert_options` (1) + `alert_payload` (6).
- Prometheus'a EKLENMEZ (YAGNI; 4 metric aile korunur).
- SPEC 164 sub_commands + SPEC 182 alert_payload_fields (restore --schema)
  AYNI (parent burada belgeler, child ayrı şemada detay).
