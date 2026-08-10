# Görev 155 — İhtiyaç

SPEC 151 `archive --schema --format prometheus` stdout basar. Grafana/
Prometheus scrape için dosya sistemine artifact yazma gerek — SPEC 145
`vault verify --schema --format prometheus --out --gzip` kalıbı.

## Kabul

- `atlas archive --schema --format prometheus --out PATH [--gzip]`.
- `--gzip` yalnız `--out` ile birlikte kullanılır → aksi SPEC HATASI
  exit 2.
- `--out` verilirse:
  - parent dizin auto-mkdir.
  - `--gzip` verilirse PATH sonuna auto-suffix `.gz` (zaten `.gz` ise değil).
  - gzip yazımı: `gzip.open(path, "wt", encoding="utf-8")`.
  - IO hatası → SPEC HATASI exit 2.
- `--out` YOKSA stdout AYNI (SPEC 151 bit-uyumlu).
- SPEC 145/155 kalıp simetrik: --gzip mutex kontrolü + auto-suffix.
