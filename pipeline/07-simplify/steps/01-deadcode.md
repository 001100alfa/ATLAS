# 01 — Ölü Kod Taraması  `/deadcode`

**Amaç:** Erişilmeyen/kullanılmayan her şeyi silmek.

| | |
|---|---|
| **Girdi** | Review'dan çıkmış kod |
| **Çıktı** | Silme commit'leri |

## Prosedür
1. vulture/coverage raporundan erişilmeyen dalları bul.
2. Kullanılmayan import, değişken, parametre -> sil.
3. 'Belki lazım olur' -> SİL. Git hatırlar, sen hatırlama.

## Kapıya Katkısı
Bakım yüzeyi küçülür.
