# Görev 163 — Teslim

`atlas vault backup --schema --format prometheus --out PATH [--gzip]`.

## Uygulama
- SPEC 158 Prometheus dalına `--out` + `--gzip` desteği (SPEC 145/155/156/162 kalıbı).
- `vbs_out` + `vbs_use_gzip` lokal; auto-suffix `.gz`; gzip.open("wt").
- Parent dizin auto-mkdir.
- MUTEX (--schema modda): `--gzip` yalnız `--out` ile → aksi SPEC HATASI exit 2.
- MUTEX (normal backup modda): `--gzip` YOK; verilirse SPEC HATASI exit 2
  (yeni MUTEX — SPEC 163 kalıbı normal modu koruyor).
- IO hatası exit 2.
- Parser: `--gzip` yeni argüman (vault backup için); `--out` help iki
  modu kapsıyor (SPEC 041 normal + SPEC 163 schema prom).
- notes: SPEC 163 satırı eklendi.

## Kanıt
- +8 test (`tests/test_cli_vault_backup_schema_prom_out.py`):
  - --out dosyaya yazar, stdout boş
  - stdout ↔ dosya içerik bit-uyumlu
  - --gzip auto-suffix + gzip.open ile okunabilir
  - Zaten .gz ise ikinci .gz eklenmez
  - --schema modda --gzip --out olmadan SPEC HATASI
  - Parent auto-mkdir (nested dizin)
  - --out YOK → SPEC 158 stdout bit-uyumlu
  - Normal backup modda --gzip → SPEC HATASI (yeni MUTEX)
- vault_backup regresyon 91 test yeşil (SPEC 041/041.1/154/158/163).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 154 JSON şeması AYNI (--format yoksa).
- SPEC 158 Prometheus stdout modu AYNI (--out yoksa).
- SPEC 041 normal `vault backup [--out PATH]` DOKUNULMADI (dispatcher
  yolu AYNI, --gzip yeni MUTEX ile reddediyor).
- SPEC 041.1/041.2/101 --auto/--keep/--encrypt/--split DOKUNULMADI.
- SPEC 161 workflow adımı (shell gzip) hâlâ çalışır; native --out
  --gzip'e taşıma sonraki tur adayı.
