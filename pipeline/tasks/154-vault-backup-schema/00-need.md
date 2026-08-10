# Görev 154 — İhtiyaç

SPEC 040/136/146/149 kalıbı vault backup için: `atlas vault backup
--schema` kısa devre JSON şema tanımı basar (backup çıktı yapısı +
exit kodları + format seçenekleri).

## Kabul

- `atlas vault backup --schema [--pretty]`.
- Vault dizini gerekmez — kısa devre (SPEC 040 kalıbı).
- JSON: `{schema_version, top_level, exit_codes, formats, notes}`.
- top_level: backup_path, vault_root, action, split_parts (opsiyonel),
  pruned_count (opsiyonel), encrypted (opsiyonel).
- exit_codes 0/2/6 (SPEC 041/041.1 kalıp).
- formats human (default; --json henüz yok — YAGNI).
- `--pretty` indent=2.
- `--schema` YOKSA SPEC 041/041.1/101 vault backup normal davranışlar
  BİT-UYUMLU.
