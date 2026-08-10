# Görev 170 — Teslim

`atlas ai-cli status <name> --alert-webhook URL`.

## Uygulama
- `_cmd_ai_cli_status` normal dispatcher'da (report üretildikten +
  MUTEX'lerden sonra, çıktı üretiminden önce) --alert-webhook POST
  (SPEC 064/165/168 kalıbı).
- Bulgu ölçütü: `up_to_date=False`.
- POST payload (SPEC 064 kalıbı):
  - `alert=ai-cli-status` + name + installed_version + declared_version
    + up_to_date=False + install_dir.
- `_post_alert_webhook()` yeniden kullanıldı.
- Başarısız POST → stderr uyarı; exit code KORUNUR.
- Stdout'a dokunmaz (--json/--json-lines/human ile ortogonal).
- SPEC 146 `--schema` kısa devre önce çalışır → --alert-webhook YOK
  sayılır schema modunda.
- Parser: `--alert-webhook URL` yeni argüman.

## Kanıt
- +7 test (`tests/test_cli_ai_cli_status_alert_webhook.py`) —
  ephemeral HTTP server + gerçek node_modules/package.json seed:
  1. up_to_date=False → POST atılır + doğru payload alanları
  2. up_to_date=True → POST atılmaz (sessiz)
  3. POST 500 → başarısız stderr; exit code KORUR
  4. Schema modda --alert-webhook YOK sayılır (POST atılmaz)
  5. SSRF savunma: file:// scheme → POST başarısız
  6. --alert-webhook YOK → SPEC 037.4 davranışı AYNI (bit-uyumlu)
  7. --json + --alert-webhook ortogonal: stdout JSON, stderr uyarı,
     POST atılır
- ai-cli regresyon 128 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 037.4 normal ai-cli status davranışı AYNI (--alert-webhook yoksa).
- SPEC 118/120 --json-lines --out --gzip DOKUNULMADI.
- SPEC 146 --schema kısa devre AYNI (webhook önce dispatcher'a ulaşmaz).
- SPEC 150/156 --format prometheus --out --gzip DOKUNULMADI.
- SPEC 064 `_post_alert_webhook()` implementasyonu AYNI (yeniden kullanıldı).
