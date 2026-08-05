# Görev 078 — Teslim

`atlas vault restore --decrypt-recipient` — GPG asimetrik decrypt-restore.

## Uygulama

- `memory/vault_backup.py::decrypt_backup_recipient(enc, out, *,
  gpg_bin)`:
  argv `gpg --batch --yes --decrypt --output <out> <enc>`. Passphrase
  YOK (private key + gpg-agent). Timeout 120s.
- `cli.py::_cmd_vault_restore`:
  - `--decrypt-recipient` (store_true) bayrağı.
  - `--decrypt` + `--decrypt-recipient` MUTEX (exit 2).
  - Auto-detect UYARI iki moda işaret.
  - Dry-run mesajı SPEC 066/078 ayrımı.
  - Audit `decrypt-recipient` action.
- Parser: `--decrypt-recipient` bayrak.

## Kanıt

- +9 test:
  - Birim `decrypt_backup_recipient` (4): kaynak yok, gpg yok, argv
    dogru (passphrase YOK), exit ≠0.
  - CLI (5): apply başarı + audit, dry-run mesajı SPEC 078,
    --decrypt+--decrypt-recipient mutex exit 2, gpg hata exit 6,
    .gpg uzantı UYARI iki moda işaret.
- Mevcut SPEC 066 test'leri 2 test güncellendi (mesaj metni SPEC 078
  ile birlikte değişti — bit-uyumluluk regex tolerans).
- 1186 → **1195 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 066 `--decrypt` symmetric BİT-UYUMLU (davranış aynı, mesaj metni
  "GPG decrypt" → "GPG symmetric decrypt" — 2 test güncellendi).
- SPEC 041/063/067/073 vault zinciri BİT-UYUMLU.
