# Görev 162 — Teslim

`atlas metrics --schema --format prometheus --out PATH [--gzip]`.

## Uygulama
- SPEC 157 Prometheus dalına `--out` + `--gzip` desteği (SPEC 145/155/156 kalıbı).
- `ms_out` + `ms_use_gzip` lokal; auto-suffix `.gz`; gzip.open("wt").
- Parent dizin auto-mkdir.
- MUTEX: `--gzip` yalnız `--out` ile → aksi SPEC HATASI exit 2.
- IO hatası exit 2.
- Parser: `--out`/`--gzip` help metinleri iki modu kapsıyor
  (SPEC 096/103 --group-by prom + SPEC 162 --schema prom).
- notes: SPEC 162 satırı eklendi.

## Kanıt
- +7 test (`tests/test_cli_metrics_schema_prom_out.py`):
  - --out dosyaya yazar, stdout boş
  - stdout ↔ dosya içerik bit-uyumlu
  - --gzip auto-suffix + gzip.open ile okunabilir
  - Zaten .gz ise ikinci .gz eklenmez
  - --gzip --out olmadan SPEC HATASI exit 2
  - Parent auto-mkdir (nested dizin)
  - --out YOK → SPEC 157 stdout bit-uyumlu
- metrics regresyon 215 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 153 JSON şeması AYNI (--format yoksa).
- SPEC 157 Prometheus stdout modu AYNI (--out yoksa).
- SPEC 096/103 --group-by --format prometheus --out --gzip DOKUNULMADI.
- SPEC 160 workflow adımı (shell gzip) hâlâ çalışır; native --out
  --gzip'e taşıma sonraki tur adayı.
