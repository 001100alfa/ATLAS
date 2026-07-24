# 03 — API Küçültme  `/api-shrink`

**Amaç:** Public yüzeyi savunulabilir minimuma indirmek.

| | |
|---|---|
| **Girdi** | Modül exports |
| **Çıktı** | Gerekçeli public API listesi |

## Prosedür
1. __all__ dışındaki her public öğe: dışarıdan çağrılıyor mu?
2. Hayırsa _private yap. Belgesiz public öğe kalmasın.
3. Her public öğe SIMPLIFY raporunda tek satır gerekçe alır.

## Kapıya Katkısı
Gate: 'public API listelendi ve gerekçeli'.
