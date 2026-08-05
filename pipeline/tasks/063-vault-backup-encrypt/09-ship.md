# Görev 063 — Teslim

`atlas vault backup --encrypt [PASSPHRASE]` — GPG symmetric AES256.

## Uygulama

- `memory/vault_backup.py`:
  - `_find_gpg_bin()`: env `ATLAS_GPG_BIN` → `tools/gpg/gpg[.exe]` →
    `shutil.which("gpg")`.
  - `encrypt_backup(plain, out, passphrase, *, gpg_bin, cipher)`:
    argv `gpg --batch --yes --symmetric --cipher-algo AES256
    --passphrase-fd 0 --output <out> <plain>`; passphrase stdin ile.
    Hata → `VaultBackupError` + gpg stderr (ilk 200 char).
- `cli.py::_cmd_vault_backup`: `--encrypt` verildiyse boş passphrase
  denetimi (exit 2), sonra `encrypt_backup` çağrısı, sonra plain silme,
  audit `atlas-vault / encrypt`.
- Parser: `--encrypt` `nargs="?"` `const=env(ATLAS_BACKUP_PASSPHRASE, "")`
  → bayraksız çağrı env'e düşer, explicit çağrı override eder.

## Kanıt

- +13 test (`tests/test_cli_vault_backup_encrypt.py`):
  - Birim `_find_gpg_bin` (2): env override, env yok fallback.
  - Birim `encrypt_backup` (5): kaynak yok, boş passphrase, gpg yok,
    argv + stdin doğru, exit ≠0, subprocess OSError.
  - CLI (5): başarı (plain silindi + .gpg mevcut), boş passphrase +
    env yok → exit 2, env passphrase kullanılır, gpg hata → exit 6,
    --encrypt yoksa bit-uyumlu.
- 1048 → **1061 yeşil**, 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 041/041.1 (backup, --auto, --keep, --out) BİT-UYUMLU.
- SPEC 048 systemd/Task Scheduler template'leri ETKİLENMEZ (kullanıcı
  isterse `--encrypt` bayrağını service'a ekler).
- Restore tarafı DEĞİŞMEDİ — kullanıcı elle `gpg --decrypt` sonra
  `atlas vault restore` çağırır (gelecek SPEC 066 aday).
