# Görev 067 — Teslim

`atlas vault backup --keep-encrypted N` — .tar.gz.gpg retention.

## Uygulama

- `memory/vault_backup.py::prune_encrypted_backups(archive_root, keep)`:
  SPEC 041.1 `prune_backups` kardeşi. Glob `vault-*.tar.gz.gpg`.
  Plain `.tar.gz` DOKUNULMAZ (ayrı havuz).
- `cli.py::_cmd_vault_backup`: `--encrypt` bloğunun ARDINDAN
  `--keep-encrypted` bloğu. Aynı `--out` uyarı kalıbı; N<1 → exit 2;
  OSError → exit 6.
- Audit: `atlas-vault / prune-encrypted / <path>`.
- Parser: `--keep-encrypted N` bayrağı (int).

## Kanıt

- +9 test (`tests/test_cli_vault_backup_keep_encrypted.py`):
  - Birim (5): keep=1 siler / keep>=toplam / plain dokunmaz /
    keep=0 → hata / arc yok → boş.
  - CLI (4): 3 mevcut + backup + --keep-encrypted 2 → 2 kalır +
    2 audit `prune-encrypted`; keep-encrypted 0 → exit 2;
    --out + --keep-encrypted → UYARI; --keep (plain) ve
    --keep-encrypted ORTOGONAL (ikisi ayrı glob'a bakar).
- 1072 → **1081 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 041/041.1/063 BİT-UYUMLU.
- Plain havuz (`vault-*.tar.gz`) retention `--keep N` üzerinden;
  encrypted havuz (`vault-*.tar.gz.gpg`) `--keep-encrypted N` üzerinden.
- Aynı çağrıda ikisi kullanılabilir.
