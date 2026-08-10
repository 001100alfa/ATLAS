# Görev 176 — Teslim

`atlas archive --restore <id> --alert-webhook URL` (SPEC 064/165/168/170 kalıbı).

## Uygulama
- `_cmd_archive_restore` başında `_emit_restore_alert()` closure —
  helper işlev (DRY, 4 hata noktasına aynı çağrı).
- 4 POST tetik noktası:
  1. `--search` regex hatası (exit 2) → SPEC HATASI + POST
  2. `--search` eşleşme yok (exit 6) → ARŞİV HATASI + POST
  3. `--search` belirsizlik (2+ eşleşme, exit 2) → SPEC HATASI + POST
  4. Arşiv bulunamadı (exit 6) → ARŞİV HATASI + POST
  5. RestoreError (çakışma exit 3 VEYA extract hatası exit 6) → POST
- POST payload: `alert=archive-restore` + task_id + search_pattern +
  archive_root + error + exit_code.
- `_post_alert_webhook()` yeniden kullanıldı.
- Başarısız POST → stderr uyarı; exit code KORUNUR.
- Başarı (exit 0) VEYA dry-run → POST YOK.
- Parser: `--alert-webhook URL` yeni argüman (archive için ilk webhook).

## Kanıt
- +8 test (`tests/test_cli_archive_restore_alert_webhook.py`) —
  gerçek tarball + ephemeral HTTP server:
  1. Arşiv bulunamadı (exit 6) → POST + task_id doğru
  2. RestoreError çakışma (exit 3) → POST + task_id doğru
  3. Başarılı restore (exit 0) → POST atılmaz (sessiz)
  4. Dry-run (--apply yok) → POST atılmaz (hedef var olsa da)
  5. --search hiç eşleşme (exit 6) → POST + search_pattern doğru
  6. --search belirsiz (exit 2) → POST + search_pattern doğru
  7. POST 500 → başarısız stderr; exit code KORUR
  8. --alert-webhook YOK → SPEC 033 davranışı AYNI (bit-uyumlu)
- archive_restore regresyon 45 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 033 normal --restore davranışı AYNI (--alert-webhook yoksa).
- SPEC 071 --search + --restore AYNI.
- SPEC 127/133/138 --json/--json-lines/--out DOKUNULMADI (stdout dokunulmaz).
- SPEC 149/151/155/164/171 --schema dalları DOKUNULMADI.
- SPEC 064 `_post_alert_webhook()` implementasyonu AYNI.
- Dry-run modda POST YOK (yalnız --apply hataları için tetiklenir).
