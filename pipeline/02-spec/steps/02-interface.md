# 02 — Arayüz Sözleşmesi  `/interface`

**Amaç:** İmzaları, birimleri ve hata davranışını sabitlemek.

| | |
|---|---|
| **Girdi** | FR tablosu |
| **Çıktı** | Python imzaları + docstring sözleşmeleri |

## Prosedür
1. Her public fonksiyon: imza + param birimleri + dönüş tipi.
2. Her hata koşulu: hangi exception, hangi mesajla.
3. Sözleşme sonradan değişirse -> spec revizyonu + onay tazeleme.

## Kapıya Katkısı
Gate: 'arayüz sözleşmesi tam' işaretlenir.
