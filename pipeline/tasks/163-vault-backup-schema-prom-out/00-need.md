# Görev 163 — İhtiyaç

SPEC 158 `vault backup --schema --format prometheus` stdout basar.
Grafana/Prometheus scrape için dosya sistemine artifact yazma gerek —
SPEC 145/155/156/162 kalıbı.

## Kabul

- `atlas vault backup --schema --format prometheus --out PATH [--gzip]`.
- `--gzip` yalnız `--out` ile birlikte kullanılır → aksi SPEC HATASI
  exit 2.
- `--out` verilirse:
  - parent dizin auto-mkdir.
  - `--gzip` verilirse PATH sonuna auto-suffix `.gz` (zaten `.gz` ise değil).
  - gzip yazımı: `gzip.open(path, "wt", encoding="utf-8")`.
  - IO hatası → SPEC HATASI exit 2.
- `--out` YOKSA stdout AYNI (SPEC 158 bit-uyumlu).
- Mevcut SPEC 041 `--out PATH` (normal backup — vault yedeği dosya
  yolu) DOKUNULMADI. --schema modu SPEC 154 kısa devre önce; normal
  backup dispatcher'a --schema modu asla girmez.
- Vault dizini gerekmez (SPEC 154 kısa devre AYNI).
