# Görev 096 — İhtiyaç

SPEC 090 `--group-by --format prometheus` grup histogram stdout'a
basıyor. CI'de scrape endpoint yerine artifact (dosya) tercih. Şu an
`> file.prom` shell redirect gerek → Windows kodlaması sorunları,
build sistemleri için "atomic write" garantisi yok.

## Kabul

- `atlas metrics --group-by KEY --format prometheus --out PATH`.
- `--out PATH` yalnız `--format prometheus` + `--group-by` ile
  birlikte anlamlı. Aksi hâlde SPEC HATASI exit 2.
- Parent dizin auto-mkdir (SPEC 092 kalıbı).
- Yazma hatası → SPEC HATASI exit 2 (net mesaj).
- Dosya içeriği stdout modu ile BİT-UYUMLU (aynı satırlar).
- `--out` verildiğinde stdout Prometheus text basmaz.
- `--out` VERİLMEZSE SPEC 090 stdout AYNI (BİT-UYUMLU).
