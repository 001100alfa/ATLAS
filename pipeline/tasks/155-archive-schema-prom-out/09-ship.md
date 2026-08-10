# Görev 155 — Teslim

`atlas archive --schema --format prometheus --out PATH [--gzip]`.

## Uygulama
- SPEC 151 Prometheus dalına `--out` + `--gzip` desteği (SPEC 145 kalıbı).
- `ar_out` + `ar_use_gzip` lokal; auto-suffix `.gz`; gzip.open("wt").
- Parent dizin auto-mkdir.
- MUTEX: `--gzip` yalnız `--out` ile → aksi SPEC HATASI exit 2.
- IO hatası exit 2.
- notes: SPEC 155 satırı eklendi.

## Kanıt
- +7 test (`tests/test_cli_archive_schema_prom_out.py`):
  - --out dosyaya yazar, stdout boş
  - stdout ↔ dosya içerik bit-uyumlu
  - --gzip auto-suffix + gzip.open ile okunabilir
  - Zaten .gz ise ikinci .gz eklenmez
  - --gzip --out olmadan SPEC HATASI exit 2
  - Parent auto-mkdir (nested dizin)
  - --out YOK → SPEC 151 stdout bit-uyumlu
- archive schema regresyon 22 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 149 JSON şeması AYNI (--format yoksa).
- SPEC 151 Prometheus stdout modu AYNI (--out yoksa).
- SPEC 105/108/138 archive --out --gzip DOKUNULMADI (--json-lines dalı).
