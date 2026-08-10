# Görev 178 — İhtiyaç

SPEC 064/165/168/170/176 alert-webhook kalıbı `vault backup` için gerek:
backup/prune/split/encrypt hatası (VaultBackupError exit 6) uzak alert.

## Kabul

- `atlas vault backup --alert-webhook URL`.
- Bulgu ölçütü: **VaultBackupError** (`backup_vault`, `prune_backups`,
  `split_backup`, encrypt/recipient hataları) → HEPSİ exit 6 döner.
- SPEC HATASI (exit 2 — kullanıcı yanlış argüman) POST atmaz
  (kullanıcı stderr'i zaten görüyor).
- Başarılı backup (exit 0) → POST atılmaz.
- POST payload (SPEC 064/165/168/170/176 kalıbı):
  ```json
  {
    "alert": "vault-backup",
    "vault_root": "<path>",
    "action": "<backup|backup-auto>",
    "phase": "<backup|prune|split|encrypt>",
    "error": "<hata mesajı>",
    "exit_code": 6
  }
  ```
- `_post_alert_webhook()` yeniden kullanılır.
- Başarısız POST → stderr uyarı; exit code KORUNUR.
- Parser: `--alert-webhook URL` yeni argüman.
- --schema modu (SPEC 154 kısa devre) POST'a girmez.
