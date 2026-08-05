# Görev 063 — İhtiyaç

Vault yedekleri düz `.tar.gz` — S3/cloud'a yüklerken içerik açık.
Kullanıcı `#credential`, `#internal` gibi notları vault'ta tutuyorsa
yedek şifresiz taşınamaz. GPG symmetric AES256 endüstri standardı.

## Kabul

- `atlas vault backup --encrypt [PASSPHRASE]`.
  - Bayraksız → `ATLAS_BACKUP_PASSPHRASE` env değerini kullanır.
  - Boş passphrase (env de yoksa) → exit 2 SPEC HATASI.
- GPG argv: `--batch --yes --symmetric --cipher-algo AES256 --passphrase-fd 0`.
- Passphrase stdin ile (`subprocess.run(..., input=passphrase)`) — komut
  satırı history'sinde görünmez.
- Çıktı `<yedek>.tar.gz.gpg`; ara plain `.tar.gz` **silinir** (secret disk'te
  bırakılmaz).
- gpg exit ≠0 → exit 6 `SIFRELEME HATASI` (SPEC 041 hata sınıfı).
- `_find_gpg_bin`: env `ATLAS_GPG_BIN` → portable `tools/gpg/gpg[.exe]` →
  `shutil.which("gpg")`.
- SPEC 041/041.1 (default backup, --auto, --keep) BİT-UYUMLU.

## Risk

- Passphrase env'de → shell history'de görünmez ama env dump'ında görünür.
  Kullanıcı `.env` dosyasında saklamalı; git'e commit yasak.
- GPG binary yoksa → hata + kullanıcı `ATLAS_GPG_BIN` veya sistem kurar.
- Restore tarafında `--decrypt` YAPMADIM — SPEC 063 kapsam dışı (kullanıcı
  `gpg --decrypt <path>.gpg > <path>` sonra `atlas vault restore` çağırır).
  Gelecek SPEC (066?) için aday.
