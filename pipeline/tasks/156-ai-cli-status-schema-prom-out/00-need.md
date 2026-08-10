# Görev 156 — İhtiyaç

SPEC 150 `ai-cli status --schema --format prometheus` stdout basar.
Grafana/Prometheus scrape için dosya sistemine artifact yazma gerek —
SPEC 145/155 kalıbı.

## Kabul

- `atlas ai-cli status --schema --format prometheus --out PATH [--gzip]`.
- `--gzip` yalnız `--out` ile birlikte kullanılır → aksi SPEC HATASI exit 2.
- `--out` verilirse:
  - parent dizin auto-mkdir.
  - `--gzip` verilirse PATH sonuna auto-suffix `.gz` (zaten `.gz` ise değil).
  - gzip yazımı: `gzip.open(path, "wt", encoding="utf-8")`.
  - IO hatası → SPEC HATASI exit 2.
- `--out` YOKSA stdout AYNI (SPEC 150 bit-uyumlu).
- Mevcut SPEC 118/120 `--out --gzip` (--json-lines dalı) DOKUNULMADI.
