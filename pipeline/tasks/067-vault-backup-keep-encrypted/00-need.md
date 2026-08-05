# Görev 067 — İhtiyaç

SPEC 041.1 `--keep N` `vault-*.tar.gz` retention'ı yaparken SPEC 063
`--encrypt` `.tar.gz.gpg` üretti. Ama encrypted retention yok — kullanıcı
`--auto --encrypt --keep 30` derse `.tar.gz` retention .gpg'e dokunmaz;
disk .gpg'lerle şişer.

## Kabul

- `atlas vault backup --keep-encrypted N` — encrypted retention.
- `prune_encrypted_backups(archive_root, keep)` yardımcı — glob
  `vault-*.tar.gz.gpg`; mtime desc + ilk N tut. Plain `.tar.gz`
  dosyalarına DOKUNMAZ (ayrı havuz).
- `--out` verilmişse retention YOK sayılır (SPEC 041.1 kalıbı).
- `N < 1` → exit 2 SPEC HATASI; prune OSError → exit 6.
- SPEC 041.1 `--keep` ile ORTOGONAL — ikisi ayrı glob'a bakar.
- Audit: `atlas-vault / prune-encrypted / <path>`.

## Risk

- `--keep` ve `--keep-encrypted` her ikisi verilirse encrypt sırası:
  backup → --keep (plain retention) → encrypt (plain silinir) →
  --keep-encrypted. Yeni encrypted dosya en yeni; --keep-encrypted N ile
  ilk N kalır.
