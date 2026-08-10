# Görev 162 — İhtiyaç

SPEC 157 `metrics --schema --format prometheus` stdout basar. Grafana/
Prometheus scrape için dosya sistemine artifact yazma gerek — SPEC
145/155/156 kalıbı.

## Kabul

- `atlas metrics --schema --format prometheus --out PATH [--gzip]`.
- `--gzip` yalnız `--out` ile birlikte kullanılır → aksi SPEC HATASI
  exit 2.
- `--out` verilirse:
  - parent dizin auto-mkdir.
  - `--gzip` verilirse PATH sonuna auto-suffix `.gz` (zaten `.gz` ise değil).
  - gzip yazımı: `gzip.open(path, "wt", encoding="utf-8")`.
  - IO hatası → SPEC HATASI exit 2.
- `--out` YOKSA stdout AYNI (SPEC 157 bit-uyumlu).
- Mevcut SPEC 096/103 `--out --gzip` (--group-by + prom dalı) DOKUNULMADI.
- SPEC 160 workflow adımı bu SPEC 162 CLI'sine gelecek turda taşınabilir
  (bu turda workflow'a dokunulmuyor).
