# Görev 078 — İhtiyaç

SPEC 066 `--decrypt PASSPHRASE` symmetric. SPEC 073 `--recipient KEY_ID`
asimetrik encrypt yaptı ama restore tarafında asimetrik decrypt yok —
kullanıcı elle `gpg --decrypt <path>.gpg > /tmp/plain.tar.gz` sonra
`atlas vault restore /tmp/plain.tar.gz --apply`.

## Kabul

- `atlas vault restore --decrypt-recipient --apply`:
  - `gpg --batch --yes --decrypt --output <tmp> <encrypted>` — passphrase
    YOK (private key + gpg-agent).
  - Temp plain restore sonrası finally silinir (SPEC 066 kalıbı).
  - Audit `decrypt-recipient` action.
- `--decrypt` + `--decrypt-recipient` MUTEX exit 2.
- `.gpg` uzantı + iki mode de yok → UYARI iki moda işaret.
- Dry-run mesajı: "GPG asimetrik decrypt (private key) → restore (SPEC 078)".

## Risk

- gpg-agent unlock yapılmamışsa gpg beklet-terminal ister; `--batch`
  ile timeout 120s → gpg exit ≠0 → SIFRELEME HATASI exit 6.
  Kullanıcı önce `gpg --list-secret-keys` ile kilit açılmalı.
