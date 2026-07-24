# 03 — Kabul Testi Tanımı  `/acceptance`

**Amaç:** Her FR'ye referans değerli kabul testi bağlamak.

| | |
|---|---|
| **Girdi** | FR + arayüz |
| **Çıktı** | FR başına: referans değer, tolerans, KAYNAK |

## Prosedür
1. Kaynak hiyerarşisi: el hesabı > standart tablosu > katalog.
2. Analitik formül: rel_tol=1e-9. Katalog karşılaştırma: tolerans gerekçeli.
3. Kaynağı olmayan FR -> 01-prompts/03-how-to'ya geri dön.

## Kapıya Katkısı
Gate: 'her FR için kabul testi' sağlanır.
