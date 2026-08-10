# Görev 178 — Teslim

`atlas vault backup --alert-webhook URL` (SPEC 064/165/168/170/176 kalıbı).

## Uygulama
- `_cmd_vault_backup` içinde `_emit_backup_alert(phase, error)` closure —
  helper işlev (SPEC 176 kalıbı, DRY).
- 5 POST tetik noktası (hepsi exit 6 VaultBackupError):
  1. `backup_vault()` (phase="backup")
  2. `prune_backups()` (phase="prune")
  3. `split_backup()` (phase="split")
  4. `encrypt_backup()` (SPEC 063 symmetric, phase="encrypt")
  5. `encrypt_backup_recipient()` (SPEC 073 asymmetric, phase="encrypt")
  6. `prune_encrypted_backups()` (SPEC 067, phase="prune")
- POST payload: `alert=vault-backup` + vault_root + action
  (backup|backup-auto) + phase + error + exit_code.
- SPEC HATASI (exit 2 — argüman validasyon, vault yok) POST ATMAZ
  (kullanıcı stderr'i zaten görüyor, monitoring alarmı değil).
- `_post_alert_webhook()` yeniden kullanıldı.
- Başarısız POST → stderr uyarı; exit code KORUNUR.
- --schema modu (SPEC 154 kısa devre) helper'a girmez.
- Parser: `--alert-webhook URL` yeni argüman.

## Kanıt
- +9 test (`tests/test_cli_vault_backup_alert_webhook.py`) —
  gerçek vault + monkeypatch `backup_vault`/`prune_backups`:
  1. Başarılı backup (exit 0) → POST atılmaz
  2. VaultBackupError (exit 6) → POST + phase=backup
  3. --auto → payload.action="backup-auto"
  4. prune_backups error → phase=prune
  5. SPEC HATASI --keep 0 (exit 2) → POST atmaz
  6. Vault dizini yok (exit 2) → POST atmaz
  7. POST 500 → başarısız stderr; exit code KORUR
  8. Schema modda --alert-webhook YOK sayılır
  9. --alert-webhook YOK → SPEC 041 davranışı AYNI (bit-uyumlu)
- vault_backup regresyon 102 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 041 normal backup davranışı AYNI (--alert-webhook yoksa).
- SPEC 041.1 --auto/--keep DOKUNULMADI (audit action AYNI).
- SPEC 041.2 --encrypt/--recipient DOKUNULMADI.
- SPEC 067 --keep-encrypted DOKUNULMADI.
- SPEC 101 --split DOKUNULMADI.
- SPEC 154/158/163 --schema/--format prometheus/--out --gzip DOKUNULMADI.
- SPEC HATASI (exit 2) POST atmaz — SPEC 176'da atarken (belirsizlik
  monitoring için değerli), SPEC 178'de atmaz (argüman validasyon).
