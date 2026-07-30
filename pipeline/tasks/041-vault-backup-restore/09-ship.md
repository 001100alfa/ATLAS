# Görev 041 — Teslim

Yeni modül `atlas_core/memory/vault_backup.py` + iki CLI komutu.

## Uygulama
- `backup_vault(vault_root, out_path) -> Path` — `tarfile.open` +
  `arcname="vault"` sabit kök.
- `default_backup_path(archive_root) -> Path` — timestamp'li varsayılan.
- `restore_vault(tar_path, target_root) -> Path` — temp dir'e extract
  + kanonik `vault/` alt-dizininden rename; her üye elle kontrol
  (traversal, kolon, kök).
- `VaultBackupError` yeni tip (N818 uyumlu).
- CLI: `atlas vault backup [--out] [--vault-root] [--archive-root]`
- CLI: `atlas vault restore <tar> [--apply] [--vault-root]`

## Yeni exit kodları
- `3` = restore çakışma (hedef var + boş değil)
- `6` = restore extract hatası / backup yazma hatası

## Kanıtlar
- Backup: `.tar.gz` içinde `vault/notes/a.md` var
- Restore: dosyalar geri okundu, içerik aynı
- Path traversal (`../evil`) → hata
- Beklenmeyen kök (`baska/x.md`) → hata
- Çakışma (hedef mevcut+dolu) → CLI exit 3
- Backup audit satırı: `atlas-vault` / `backup`
- +14 test (756 yeşil, cov %90.80)

## Değişmeyen sözleşme
- Mevcut `Vault` API'sı dokunulmadı.
- `atlas archive` (007/012/033) bit-uyumlu.
