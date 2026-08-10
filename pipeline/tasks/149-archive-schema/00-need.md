# Görev 149 — İhtiyaç

SPEC 136/146 kalıbı archive için: `atlas archive --schema` kısa devre
JSON şema tanımı (SPEC 040 doctor kalıbı).

## Kabul

- `atlas archive --schema [--pretty]`.
- Arşiv kökü gerekmez — kısa devre (SPEC 040 kalıbı).
- JSON: `{schema_version, top_level, exit_codes, formats, notes}`.
- top_level 7 alan (SPEC 075 `_list_archive_entries` şeması AYNI).
- exit_codes 0/2/3/6.
- formats human/json/json-lines.
- `--pretty` indent=2.
- `--schema` YOKSA SPEC 007/012/033/065/071/075 archive komutları
  BİT-UYUMLU.
