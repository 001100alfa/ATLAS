# Görev 066 — Teslim

`atlas vault restore --decrypt` — GPG decrypt-restore-cleanup zinciri.

## Uygulama

- `memory/vault_backup.py::decrypt_backup(enc, out, passphrase, *,
  gpg_bin)`: SPEC 063 `encrypt_backup` kardeşi. `gpg --batch --yes
  --decrypt --passphrase-fd 0 --output <out> <enc>`; passphrase stdin.
  Timeout 120s.
- `cli.py::_cmd_vault_restore`:
  - `--decrypt [PASSPHRASE]` bayrağı; env `ATLAS_BACKUP_PASSPHRASE`
    fallback (nargs="?" const=env).
  - `.gpg` uzantı + `--decrypt` YOK → UYARI (auto-detect nazikliği).
  - Boş passphrase → exit 2 SPEC HATASI.
  - Temp plain dosya: `<target.parent>/.vault-restore-decrypt-<pid>.tar.gz`.
    Restore sonrası **finally** ile silinir (secret disk'te bırakılmaz).
  - Audit: `atlas-vault / decrypt / <path>` + normal `restore`.
- Parser: `--decrypt` bayrağı (SPEC 063 --encrypt kalıbı).

## Kanıt

- +11 test (`tests/test_cli_vault_restore_decrypt.py`):
  - Birim `decrypt_backup` (5): kaynak yok, boş passphrase, gpg yok,
    argv+stdin doğru, exit ≠0.
  - CLI (6): apply başarı (restore + audit + temp silindi), dry-run
    "GPG decrypt → restore" mesajı, boş passphrase exit 2, gpg hata
    exit 6, .gpg uzantı + --decrypt yok → UYARI, --decrypt yoksa
    plain bit-uyumlu.
- 1081 → **1092 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 041/063 BİT-UYUMLU (default plain restore + encrypt).
- Exit kodları: 0/2/3/6 (mevcut sınıf; 6 GPG decrypt hatası dahil).
