# Görev 166 — Teslim

`atlas doctor --schema --format json-lines [--out PATH [--gzip]]`.

## Uygulama
- `_cmd_doctor` --schema bloğuna `--format json-lines` dalı eklendi
  (SPEC 087/126 kalıbı, SPEC 128 Prometheus dalı ile paralel).
- NDJSON stream: her top_level/quality_field/backend_option/env/exit_code
  bir satır + son satır summary (count'lar dahil).
- `--out PATH [--gzip]` desteklenir (SPEC 145/155/156/162 kalıbı):
  parent auto-mkdir + auto-suffix .gz + gzip.open("wt"); IO hatası exit 2.
- Mevcut SPEC 134 `--schema --out yalnız --format prometheus` MUTEX
  genişletildi: **"prometheus VEYA json-lines"**.
- MUTEX: `--format json-lines` yalnız `--schema` ile birlikte; normal
  doctor modunda REDDEDİR (SPEC HATASI exit 2, SPEC 158 kalıbı).
- Parser: `--format` choices'a `json-lines` eklendi (mevcut human/
  prometheus'a).

## Kanıt
- +9 test (`tests/test_cli_doctor_schema_jsonl.py`):
  1. NDJSON stream — son satır summary + tip çeşitliliği
  2. summary sayıları stream'deki tip dağılımına eşit
  3. top_level satırlarında name/field_type/desc alanları
  4. --out ile PATH'e stream + stdout boş
  5. --gzip auto-suffix .gz + gzip.open ile okunabilir
  6. --gzip --out olmadan SPEC HATASI exit 2
  7. Normal doctor + --format json-lines SPEC HATASI (yeni MUTEX)
  8. --format YOK → SPEC 040 JSON default bit-uyumlu
  9. SPEC 128 --format prometheus çıktısı DOKUNULMADI
- doctor regresyon 297 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 040 JSON default (--format yoksa) AYNI.
- SPEC 128 Prometheus çıktısı AYNI.
- SPEC 134 --schema prom --out --gzip yolu AYNI.
- SPEC 142 backend_options + retry_pricing_envs + storage_envs alanları
  JSON default'ta AYNI; json-lines dalında AYRI satırlar olarak stream.
- SPEC 047 normal doctor --format prometheus (metrics-like) AYNI —
  yalnız yeni `json-lines` seçimi --schema olmadan REDDEDİR.
