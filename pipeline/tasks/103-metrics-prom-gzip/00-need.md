# Görev 103 — İhtiyaç

SPEC 096 `metrics --group-by --format prometheus --out PATH` düz metin
dosya yazar. CI artifact / long-term storage için gzip sıkıştırma
çokça küçük dosya sağlar (10-100x). Prometheus scrape zaten gzip
uyumludur (`Accept-Encoding: gzip`).

## Kabul

- `atlas metrics --group-by KEY --format prometheus --out PATH --gzip`.
- `--gzip` yalnız `--out` ile birlikte anlamlı → aksi SPEC HATASI
  exit 2.
- PATH `.gz` uzantısına sahip DEĞİLSE otomatik `.gz` eklenir (kullanıcı
  şaşırmasın). Sahipse aynen kullanılır.
- Yazma: `gzip.open(op, "wt", encoding="utf-8")` — Windows/POSIX uyumlu.
- Gzip dosya içeriği decompress edildiğinde SPEC 096 düz metin ile
  BİT-UYUMLU.
- `--gzip` VERİLMEZSE SPEC 096 BİT-UYUMLU (düz metin).
