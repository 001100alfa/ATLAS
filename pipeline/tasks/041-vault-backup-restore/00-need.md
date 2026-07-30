# Görev 041 — İhtiyaç

`vault/` dizini ATLAS'ın uzun-vadeli belleği (Obsidian-uyumlu). Şu an
yedekleme mekanizması YOK — dizin silinirse veya bozulursa geçmiş
kaybolur.

## Kabul kriteri
- `atlas vault backup [--out PATH]` → `.tar.gz` sarma.
  - `--out` yok → varsayılan `<archive_root>/vault-YYYY-MM-DD-HHMM.tar.gz`.
  - Vault yok → exit 2 SPEC HATASI.
  - Audit satırı: `atlas-vault` / `backup` / `<path>`.
- `atlas vault restore <tar> [--apply]` → dry-run varsayılan.
  - `--apply` gerekli (yıkıcı işlem).
  - Hedef mevcut + boş değil → exit 3.
  - Tar yok / path traversal / kolon / kök yanlış → exit 6.
  - Audit satırı: `atlas-vault` / `restore` / `<path>`.
- Path traversal koruması (SPEC 033 kalıbı): `..`, mutlak yol, kolon
  (Windows NTFS ADS), tar kökü sabit `vault/`.
- `filter="data"` güvenli extract (Python 3.12+).

## Riskli
- Restore mevcut bir vault'un üstüne yazmamalı — bu yüzden temp dir
  extract + rename kalıbı; hedef boş olması ön koşul.
- Windows'ta rename cross-volume olabilir — testte tmp_path aynı disk
  olduğu için sorun yok; canlıda `ATLAS_VAULT` farklı diskse rename
  patlarsa `shutil.move` yedeklemesi düşünülebilir (şu an YAGNI).
