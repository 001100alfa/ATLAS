# Görev 168 — Teslim

`atlas doctor --alert-webhook URL`.

## Uygulama
- `_cmd_doctor` ana rapor sonunda `--strict` kontrolünden ÖNCE webhook POST
  (SPEC 064/165 kalıbı).
- Bulgu ölçütü: `_has_quality_warning(report)` True (quality.* alt-dict'-
  lerinden en az birinde `warning` alanı).
- POST payload: `alert=doctor` + `warnings` (üst düzey list) +
  `quality_warnings` (`{field: message}` dict).
- `_post_alert_webhook()` yeniden kullanıldı (stdlib urllib.request,
  SSRF savunma, 5s timeout).
- Başarısız POST → stderr uyarı; exit code KORUNUR.
- --strict ile ORTOGONAL (webhook exit 9'u etkilemez).
- Parser: `--alert-webhook URL` yeni argüman.
- **Sınırlama**: Yalnız ana `_cmd_doctor` sağlık raporu için (diff/history/
  ping alt dispatcher'ları YAGNI — ileri SPEC'te).

## Kanıt
- +7 test (`tests/test_cli_doctor_alert_webhook.py`) — deterministik
  monkeypatch (`_has_quality_warning`) + ephemeral HTTP server:
  1. Bulgu (warning True) varsa POST atılır + payload alanları
  2. Temiz ortam (warning False) → POST atılmaz (sessiz)
  3. POST 500 → başarısız stderr; exit code KORUR
  4. `--strict` ile birlikte: POST atılır + exit 9 (ortogonal)
  5. --alert-webhook YOK → SPEC 021 doctor davranışı AYNI (bit-uyumlu)
  6. Parser --alert-webhook argümanını kabul eder (help satırı)
  7. SSRF savunma: file:// scheme → POST başarısız
- doctor regresyon 304 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 021 normal doctor davranışı AYNI (--alert-webhook yoksa).
- SPEC 032 --strict exit 9 semantiği AYNI (webhook ortogonal).
- SPEC 040/128/134/142/166 --schema dalları DOKUNULMADI.
- SPEC 057/091/097/100/110/130 diff/history dalları DOKUNULMADI.
- SPEC 064 `_post_alert_webhook()` implementasyonu AYNI (yeniden kullanıldı).
