# Görev 066 — İhtiyaç

SPEC 063 `--encrypt` vault yedeğini GPG symmetric ile `.tar.gz.gpg`
üretiyor. Ama restore tarafında decrypt otomatik değil — kullanıcı:
```
gpg --decrypt vault-2026-08-05.tar.gz.gpg > /tmp/plain.tar.gz
atlas vault restore /tmp/plain.tar.gz --apply
rm /tmp/plain.tar.gz
```
3 komut. Otomatik decrypt-restore-cleanup zinciri gerek.

## Kabul

- `atlas vault restore <path.tar.gz.gpg> --decrypt [PASSPHRASE] --apply`:
  - GPG symmetric decrypt → temp `.tar.gz` (target parent'inde, gizli
    prefix) → restore_vault → temp silinir (finally).
  - `--decrypt` bayraksız + env `ATLAS_BACKUP_PASSPHRASE`.
  - Boş passphrase → exit 2.
  - `--decrypt` YOK + path `.gpg` uzantı → UYARI (auto-detect nazikliği;
    restore extract yine hata verecek).
- Dry-run: "GPG decrypt → restore (SPEC 066)" mesajı.
- Audit: `atlas-vault / decrypt / <path>` + `restore`.
- `decrypt_backup(enc, out, passphrase, *, gpg_bin)` yardımcı (SPEC 063
  `encrypt_backup` kardeşi; `gpg --decrypt --passphrase-fd 0`).
- Temp plain dosya restore sonrası SILINIR (secret disk'te bırakılmaz;
  finally garantili).

## Risk

- Restore çakışması (hedef boş değil) durumunda temp plain silinmelidir
  — finally block bunu garanti eder.
- .gpg uzantısı olmayan encrypted dosya için auto-detect yapılmaz —
  kullanıcı explicit `--decrypt` verir.
