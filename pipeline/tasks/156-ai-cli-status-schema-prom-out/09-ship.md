# Görev 156 — Teslim

`atlas ai-cli status --schema --format prometheus --out PATH [--gzip]`.

## Uygulama
- SPEC 150 Prometheus dalına `--out` + `--gzip` desteği (SPEC 145/155 kalıbı).
- `as_out` + `as_use_gzip` lokal; auto-suffix `.gz`; gzip.open("wt").
- Parent dizin auto-mkdir.
- MUTEX: `--gzip` yalnız `--out` ile → aksi SPEC HATASI exit 2.
- IO hatası exit 2.
- Parser: `--out` ve `--gzip` help metinleri iki modu kapsıyor (SPEC 118/120/156).
- notes: SPEC 156 satırı eklendi.

## Kanıt
- +7 test (`tests/test_cli_ai_cli_status_schema_prom_out.py`):
  - --out dosyaya yazar, stdout boş
  - stdout ↔ dosya içerik bit-uyumlu
  - --gzip auto-suffix + gzip.open ile okunabilir
  - Zaten .gz ise ikinci .gz eklenmez
  - --gzip --out olmadan SPEC HATASI exit 2
  - Parent auto-mkdir (nested dizin)
  - --out YOK → SPEC 150 stdout bit-uyumlu
- ai-cli status regresyon 41 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 146 JSON şeması AYNI (--format yoksa).
- SPEC 150 Prometheus stdout modu AYNI (--out yoksa).
- SPEC 118/120 --json-lines --out --gzip DOKUNULMADI.
