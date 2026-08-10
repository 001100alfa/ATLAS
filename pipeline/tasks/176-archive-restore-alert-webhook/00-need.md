# Görev 176 — İhtiyaç

SPEC 064/165/168/170 alert-webhook kalıbı `archive --restore` için
gerek: restore başarısızlığı (RestoreError exit 3/6, arşiv bulunamadı
exit 6, --search eşleşme yok exit 6, --search belirsiz exit 2) uzak
alert.

## Kabul

- `atlas archive --restore <id> --alert-webhook URL`.
- Bulgu ölçütü: RestoreError (exit 3 çakışma VEYA exit 6 extract
  hatası) VEYA arşiv bulunamadı (exit 6) VEYA `--search` sonuç yok
  (exit 6). `--search` belirsizlik (exit 2) DAHİL (kullanıcı yanlış
  daraltma yapmış).
- Başarılı restore (exit 0) veya dry-run → POST atılmaz (sessiz).
- POST payload (SPEC 064/165/168/170 kalıbı):
  ```json
  {
    "alert": "archive-restore",
    "task_id": "<id|null>",
    "search_pattern": "<pattern|null>",
    "archive_root": "<path>",
    "error": "<hata mesajı>",
    "exit_code": <int 2|3|6>
  }
  ```
- `_post_alert_webhook()` yeniden kullanılır.
- Başarısız POST → stderr uyarı; exit code KORUNUR.
- Parser: `--alert-webhook URL` yeni argüman (archive için ilk
  webhook).
- --json / --json-lines ile ORTOGONAL (stdout dokunulmaz).
- Dry-run modda etkisiz (--apply yoksa hiç POST yok).
