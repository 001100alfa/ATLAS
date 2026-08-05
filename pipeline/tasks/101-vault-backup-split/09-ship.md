# Görev 101 — Teslim

`atlas vault backup --split SIZE_MB [--out PATH]`.

## Uygulama

- Yeni yardımcı `vault_backup.split_backup(src, size_mb)`:
  - Fixed-size parçalar `<src>.001`, `<src>.002`, ... (3 haneli).
  - Orijinal `src` silinir (space tasarrufu).
  - `size_mb < 1` → `VaultBackupError`.
  - Boş src (0 byte) → tek boş `.001` parça (birleştirme sözleşmesi
    korunur).
- `_cmd_vault_backup`:
  - `--split` doğrulama (>=1) + `--encrypt`/`--recipient` MUTEX exit 2.
  - Retention'dan sonra, encrypt'ten önce split çalışır.
  - Split akışı `return 0` — encrypt/keep-encrypted dallarına girmez.
- Parser: `--split SIZE_MB` type=int metavar.

## Kanıt

- +11 test (`tests/test_cli_vault_backup_split.py`):
  - split_backup birim: küçük tek parça, büyük 3 parça,
    size_mb geçersiz, src yok.
  - CLI: küçük vault + split → tek parça `.001`, orijinal silindi.
  - `--split 0` → exit 2.
  - `--split --encrypt` MUTEX exit 2.
  - `--split --recipient` MUTEX exit 2.
  - `--split --out PATH` ORTOGONAL.
  - `--split YOKSA` SPEC 041 BİT-UYUMLU (tek `.tar.gz`).
  - `--keep 1 --split` retention önce (parçalar dahil değil).
- 1355 → **1366 yeşil** (+11), 12 skip.
- cov %91.39, mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 041: `--split` yoksa tek `.tar.gz` AYNI.
- SPEC 041.1: `--keep` retention AYNI (split öncesi).
- SPEC 063/073: `--encrypt`/`--recipient` split ile MUTEX (dokümante).
