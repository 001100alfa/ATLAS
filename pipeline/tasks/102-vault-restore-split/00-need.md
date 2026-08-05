# Görev 102 — İhtiyaç

SPEC 101 `vault backup --split SIZE_MB` parçalı yedek üretir. Restore
tarafında kullanıcı elle `cat *.001 > full.tar.gz` yapıp restore
etmek zorunda — Windows'ta `copy /b` ayrı komut, kodlaması karmaşık.
Native `--split` restore bayrağı gerek.

## Kabul

- `atlas vault restore <first_part.001> --split [--apply]`.
- `<first_part>` `.001` uzantılı olmalı (deterministik başlangıç).
  Aksi hâlde SPEC HATASI exit 2.
- Yeni yardımcı `vault_backup.combine_split_parts(first_part) -> Path`:
  - `.001`, `.002`, ... sıralı okur, `<base>` tek dosyaya birleştirir.
  - Boş parça listesi / eksik sıra → `VaultBackupError`.
  - Sonuç geçici dosya (restore sonrası silinir; SPEC 066 kalıbı).
- `--split` + `--decrypt`/`--decrypt-recipient` MUTEX exit 2 (encrypted
  split ayrı SPEC — YAGNI, SPEC 101 simetrisi).
- Dry-run (`--apply` yok) → birleştirme YAPILMAZ, sadece plan basılır.
- Apply sonrası birleştirilen tmp dosya silinir (finally).
- Split parçaları KORUNUR (silinmez) — kullanıcı yedek kaynak.
- `--split` VERİLMEZSE SPEC 041/066 BİT-UYUMLU.
