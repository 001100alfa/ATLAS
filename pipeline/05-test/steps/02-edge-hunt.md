# 02 — Kenar Avcısı  `/edge-hunt`

**Amaç:** Sıfır, negatif, sınır, taşma senaryolarını taramak.

| | |
|---|---|
| **Girdi** | Arayüz sözleşmesi |
| **Çıktı** | Parametrize kenar durum testleri |

## Prosedür
1. Her sayısal param için: 0, negatif, çok küçük, çok büyük.
2. Geometrik tutarsızlıklar: hw<=0, t>b/2 gibi alan kuralları.
3. Her kenar ya doğru sonuç ya TANIMLI hata vermeli — sessiz yanlış YASAK.

## Kapıya Katkısı
Gate: kenar durumlar kapsandı.
