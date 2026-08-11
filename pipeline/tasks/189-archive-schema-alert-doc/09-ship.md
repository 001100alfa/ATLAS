# Görev 189 — Teslim

`archive --schema` JSON'a `alert_options` (1) + `alert_payload` (6).

## Uygulama
- SPEC 175/181/188 kalıbı archive parent şeması için.
- SPEC 176 --restore --alert-webhook payload alanları belgelendi.
- Prometheus'a EKLENMEDİ (YAGNI).
- notes: SPEC 176 + SPEC 189.

## Kanıt
- +5 test; archive_schema regresyon 38 yeşil.

## Not
SPEC 182 restore-özel şeması `alert_payload_fields` alanına AYNI 6 alanı
zaten koyar; SPEC 189 parent şemada TEKRAR eder — kullanıcı
`archive --schema` çıktısından hem sub_commands hem alert_payload'ı
görür (`--restore --schema`'ya inmeden).
