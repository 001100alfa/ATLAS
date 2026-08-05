# Görev 073 — İhtiyaç

SPEC 063 `--encrypt PASSPHRASE` symmetric — passphrase paylaşımı
insan/env kanalı gerektirir. Çok-kullanıcı deployment'ta her kullanıcı
kendi GPG public key'ini paylaşır → asimetrik (`gpg --encrypt -r <key>`)
zero-secret-share çözüm.

## Kabul

- `atlas vault backup --recipient KEY_ID`:
  - GPG public-key encryption (`gpg --encrypt --recipient <KEY_ID>
    --trust-model always`).
  - Passphrase YOK (recipient keyring'te olmalı).
  - `--trust-model always` — CI/automation için trust prompt bypass.
  - Çıktı `<yedek>.tar.gz.gpg`; plain silinir (SPEC 063 kalıbı).
- `--encrypt` ve `--recipient` MUTEX → exit 2.
- Audit: `encrypt-recipient` action.
- SPEC 041/041.1 (default plain, --auto, --keep) BİT-UYUMLU.
- SPEC 067 `--keep-encrypted` .gpg retention iki modu da (symmetric/
  asimetrik) kapsar (aynı glob).

## Risk

- Recipient KEY_ID keyring'te değilse gpg exit ≠0 → SIFRELEME HATASI
  exit 6.
- SPEC 066 `--decrypt` symmetric passphrase-fd kalıbı — asimetrik
  decrypt için private key + gpg-agent gerek (gelecek SPEC 078 aday).
- `--trust-model always` güvenlik zayıflaması sayılmaz çünkü kullanıcı
  bilinçli `--recipient` verdi.
