# Görev 033 — Teslim

`atlas archive --restore <id> [--apply]` komutu eklendi. `.tar.gz`
extract `filter="data"` güvenli mod ile; ek olarak arşiv okurken her
üye elle kontrol edilir (path traversal, kolon, beklenmeyen kök).

## Yeni exit kodları
- 3 → çakışma (hedef zaten var)
- 6 → arşiv yok VEYA extract hatası (RestoreError)

## Kanıtlar
- `_find_archive_for_task`: yok → None; iki tar → en yeni mtime
- `restore_task`: başarı, arşiv yok, hedef var, path traversal, kolon,
  beklenmeyen kök
- CLI: dry-run plan, apply başarı + audit, arşiv yok exit 6, çakışma
  exit 3
- +12 test (705 yeşil, cov %90.76)

## Değişmeyen sözleşme
- `atlas archive <task>` ve `atlas archive --all` bit-uyumlu.
- `archive_task` fonksiyonu dokunulmadı.
- `RestoreError` yeni tip (N818 uyumlu).
