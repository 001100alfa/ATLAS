# Görev 102 — Teslim

`atlas vault restore <first.001> --split [--apply]`.

## Uygulama

- Yeni yardımcı `vault_backup.combine_split_parts(first_part)`:
  - `.001` başlar, `.NNN` sıralı okur, tek dosyaya birleştirir.
  - Sonuç: geçici dosya `<base>.combined-<pid>` (restore sonrası siler).
  - `.001` uzantı YOKSA / ilk parça YOK / hiç parça yok → VaultBackupError.
  - Parçaların **orijinali korunur** (silinmez).
- `_cmd_vault_restore`:
  - `--split` + `--decrypt`/`--decrypt-recipient` MUTEX exit 2.
  - `<path>` `.001` DEĞİLSE SPEC HATASI exit 2.
  - Dry-run → birleştirme YAPILMAZ, plan basılır.
  - Apply: `combine_split_parts` → `plain_path` → `restore_vault` →
    finally tmp_plain silinir (SPEC 066 kalıbı).
- Parser: `--split` action="store_true".

## Kanıt

- +11 test (`tests/test_cli_vault_restore_split.py`):
  - `combine_split_parts` birim: temel (3 parça),
    yanlış uzantı, ilk parça yok, tek parça.
  - CLI: --split apply → hedef vault içerik doğru.
  - --split dry-run → plan mesajı.
  - `.001` yerine `.tar.gz` → exit 2.
  - --split + --decrypt MUTEX exit 2.
  - --split + --decrypt-recipient MUTEX exit 2.
  - Parçalar restore sonrası KORUNUR.
  - --split YOKSA SPEC 041 restore AYNI.
- 1396 → **1407 yeşil** (+11), 12 skip.
- cov %91.37, mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 041/066/078: mevcut restore/decrypt akışları AYNI.
- SPEC 101: `split_backup` DOKUNULMADI (sadece kardeş helper eklendi).
- Parçalar korunur (kullanıcı için ek yedek).
