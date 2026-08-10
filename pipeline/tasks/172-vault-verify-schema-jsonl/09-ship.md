# Görev 172 — Teslim

`atlas vault verify --schema --format json-lines [--out PATH [--gzip]]`.

## Uygulama
- `_cmd_vault_verify` --schema bloğuna `--format json-lines` dalı
  (SPEC 087/126/166/171 kalıbı).
- NDJSON stream: her top_level/exit_code/format bir satır + summary.
- SPEC 087 normal `vault verify --format json-lines` (bulgu NDJSON)
  DOKUNULMADI — `--schema` flag'i iki farklı davranışı ayırır (schema
  şeması vs bulgu şeması).
- `--out PATH [--gzip]` desteği (SPEC 145/166/171 kalıbı).
- Parser DEĞİŞMEDİ — `--format json-lines` choices'da mevcut (SPEC 087).
- notes: SPEC 172 satırı eklendi.

## Kanıt
- +9 test (`tests/test_cli_vault_verify_schema_jsonl.py`):
  1. NDJSON stream — son satır summary + tip çeşitliliği
  2. summary sayıları stream tip dağılımına eşit
  3. top_level 6 alan (notes/links/tags/broken/orphan_notes/orphan_tags)
  4. --out ile PATH'e stream + stdout boş
  5. --gzip auto-suffix .gz + gzip.open ile okunabilir
  6. --gzip --out olmadan SPEC HATASI exit 2
  7. --schema YOK + --format json-lines → normal SPEC 087 davranışı AYNI
     (vault yoksa SPEC HATASI)
  8. --format YOK → SPEC 136 JSON default bit-uyumlu
  9. SPEC 140 --format prometheus çıktısı DOKUNULMADI
- vault_verify regresyon 92 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 087 normal `vault verify --format json-lines` (bulgu NDJSON)
  AYNI — --schema dal ayırır.
- SPEC 136 JSON default şeması AYNI (--format yoksa).
- SPEC 140 Prometheus çıktısı AYNI.
- SPEC 145 --out --gzip (Prometheus için) yolu AYNI.
- SPEC 042 normal vault verify davranışı AYNI.
- SPEC 052/092/111 --dump-report/--out/--gzip DOKUNULMADI.
