# 03 — Sıralama  `/sequence`

**Amaç:** Bağımlılık grafiği + fail-fast sıra.

| | |
|---|---|
| **Girdi** | WP + risk |
| **Çıktı** | Sıralı yürütme listesi |

## Prosedür
1. Bağımlılıkları çiz: WP-x, WP-y'yi bekliyor mu?
2. EN RİSKLİ bağımsız paket İLK — erken batacaksa ucuz batsın.
3. Paralelleştirilebilir paketleri işaretle (subagent adayı).

## Kapıya Katkısı
Gate: 'en riskli paket ilk' sağlanır.
