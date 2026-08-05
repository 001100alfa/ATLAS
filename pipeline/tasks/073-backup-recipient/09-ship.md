# Görev 073 — Teslim

`atlas vault backup --recipient KEY_ID` — GPG public-key encryption.

## Uygulama

- `memory/vault_backup.py::encrypt_backup_recipient(plain, out,
  recipient, *, gpg_bin)`:
  argv `gpg --batch --yes --encrypt --recipient <KEY> --trust-model
  always --output <out> <plain>`. Passphrase YOK (asimetrik).
  Timeout 120s. Hata → `VaultBackupError`.
- `cli.py::_cmd_vault_backup`:
  - `--encrypt` ve `--recipient` MUTEX (exit 2).
  - `--recipient` verildiyse `encrypt_backup_recipient` çağrısı;
    audit `encrypt-recipient`; plain silinir.
- Parser: `--recipient KEY_ID` bayrağı (SPEC 063 kalıbı ama passphrase
  YOK).

## Kanıt

- +9 test (`tests/test_cli_vault_backup_recipient.py`):
  - Birim (5): kaynak yok, boş recipient, gpg yok, argv doğru
    (--recipient + --trust-model always + passphrase YOK), exit ≠0.
  - CLI (4): apply başarı + audit, --encrypt+--recipient mutex exit 2,
    gpg hata exit 6, --recipient yoksa plain bit-uyumlu.
- 1154 → **1163 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 041/041.1/063/066/067 hepsi BİT-UYUMLU.
- SPEC 067 `--keep-encrypted` .gpg glob'u iki mod (symmetric/asimetrik)
  için de çalışır (uzantı aynı).
