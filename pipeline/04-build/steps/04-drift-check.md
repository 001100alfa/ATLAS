# 04 — Sapma Dedektörü  `/drift-check`

**Amaç:** Spec dışına kaymayı erken yakalamak.

| | |
|---|---|
| **Girdi** | Güncel diff + SPEC |
| **Çıktı** | Sapma raporu (temiz / sapma var) |

## Prosedür
1. Her 2-3 WP'de bir: diff'teki her public öğe spec'te var mı?
2. Spec'te olmayan özellik -> ya sil ya spec revizyonu (onaylı).
3. 'Madem elim değmişken' kodu = sapma. İstisna yok.

## Kapıya Katkısı
Gate: 'spec'ten sapma yok/işlendi' sağlanır.
