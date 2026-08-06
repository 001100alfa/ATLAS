# Görev 136 — İhtiyaç

SPEC 042 `vault verify` çıktı şeması `to_dict()` sözleşmesi kodda ama
doküman/tüketici için `--schema` bayrağı (SPEC 040 doctor kalıbı) yok.

## Kabul

- `atlas vault verify --schema [--pretty]`.
- Vault dizini gerekmez (kısa devre; SPEC 040 kalıbı).
- JSON: `{schema_version, top_level:[{name,type,desc}], exit_codes,
  formats, notes}`.
- Diğer bayraklar (`--strict/--out/--gzip/--format`) --schema ile
  birlikte YOKSAYILIR (kısa devre önce).
- `--schema` YOKSA SPEC 042 verify AYNI (bit-uyumlu).
