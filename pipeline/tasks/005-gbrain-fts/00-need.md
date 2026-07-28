# 005 — İhtiyaç: GBrain SQLite-FTS indeksi

## Bağlam
`GBrain.recall()` her çağrıda tüm notları diskten okuyup her kelimeyi
`str.count()` ile sayıyor (`gbrain.py:85-95`). 20 notta önemsiz, 500'de
fark edilir, 2000'de dayanılmaz. `Vault.graph()` de her çağrıda tüm
`.md` dosyalarını yeniden okuyor. Ölçeklenmez.

## İhtiyaç (tek cümle)
GBrain FTS destekli hızlı arama versin; vault gerçek kaynak olarak
kalsın, indeks önbellek olsun; stale olunca **otomatik** yeniden kurulsun.

## Ölçülebilir Başarı
- **M1:** 500 notta `recall("kelime")` < 50 ms (mevcut O(N·M) yaklaşımdan
  ≥ 10× hız).
- **M2:** Yeni not eklenip indeks stale kaldığında `recall()` çağrısı
  otomatik reindex tetikler; kullanıcı hiçbir şey yapmaz.
- **M3:** Sonuçlar mevcut `recall()` sözleşmesiyle uyumlu (`list[Recall]`,
  aynı skor semantiği: FTS rank + graf komşuluğu).
- **M4:** `atlas reindex` komutu manuel yeniden kurulum imkânı verir.
- **M5:** Testler yeşil (yeni + regresyon); coverage ≥ %90.

## Kapsam DIŞI
- Semantik/embedding araması (Görev 010+).
- Türkçe tokenizer/stemmer — FTS5 unicode61 varsayılanı yeterli.
- Not silme (vault silme desteklemiyor; indeks sadece upsert).

## Kısıt
- `GBrain` **sözleşmesi değişmez**: `recall()`, `remember()`,
  `context_for()`, `log_event()` imzaları korunur.
- İndeks dosyası `.atlas/gbrain.sqlite` (audit ile aynı yer, gitignore).
- stdlib-only (sqlite3, hashlib) — yeni bağımlılık yok.
