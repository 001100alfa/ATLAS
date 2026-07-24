# 06 — Anti-Halüsinasyon  `/anti-hallucination`

**Amaç:** Modeli uydurmaya itebilecek her açığı kapatmak.

| | |
|---|---|
| **Girdi** | Hizalı yönerge |
| **Çıktı** | Güvenlik kilitleri eklenmiş yönerge |

## Prosedür
1. 'Bilmiyorsan uydurma, sor' talimatını açıkça ekle.
2. Referans değeri olmayan sayısal iddia YASAK kuralı ekle.
3. Negatif örnek ekle: 'Şunu yaparsan yanlış: <örnek>'.

## Kapıya Katkısı
Gate: 'en az 1 pozitif + 1 negatif örnek' sağlanır.
