# Görev 108 — İhtiyaç

SPEC 105 `archive --list --json-lines --out PATH` düz metin NDJSON
yazar. Yüzlerce arşiv olan üretim kurulumunda `--gzip` bayrağı
(SPEC 103 kalıbı) artifact boyutunu 5-10x düşürür.

## Kabul

- `atlas archive --list --json-lines --out PATH --gzip`.
- `--gzip` yalnız `--out` ile birlikte anlamlı → aksi SPEC HATASI
  exit 2.
- PATH `.gz` uzantı yoksa auto-suffix `.gz` (SPEC 103 kalıbı).
- Yazma: `gzip.open(op, "wt", encoding="utf-8")` — NDJSON satır satır.
- Decompress edildiğinde SPEC 105 düz NDJSON ile BİT-UYUMLU.
- `--gzip` VERİLMEZSE SPEC 105 BİT-UYUMLU (düz metin).
