# 02 — Tekrar Avı  `/dedupe`

**Amaç:** Kopyala-yapıştır mantığı tekilleştirmek.

| | |
|---|---|
| **Girdi** | Kod tabanı |
| **Çıktı** | Ortak yardımcılara çekilmiş mantık |

## Prosedür
1. 3+ satırlık benzer bloklar -> tek fonksiyon adayı.
2. AMA: 2 kullanım için soyutlama ACELE olabilir — 3. kullanımı bekle.
3. Soyutlama birimleri karıştırıyorsa yapma (mm+derece tek fonksiyonda olmaz).

## Kapıya Katkısı
DRY, dogma değil muhakeme ile uygulanır.
