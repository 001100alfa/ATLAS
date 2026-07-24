# 04 — Düzeltme Turu  `/fix-round`

**Amaç:** K ve M'leri commit referanslı kapatmak.

| | |
|---|---|
| **Girdi** | Sınıflı tablo |
| **Çıktı** | Düzeltme commit'leri + güncel tablo |

## Prosedür
1. Her düzeltme ayrı commit: 'fix(REV-N): <özet>'.
2. Düzeltme sonrası İLGİLİ testler + tam set tekrar yeşil.
3. Düzeltme yeni bulgu doğurdu mu? Evetse tabloya ekle, döngü.

## Kapıya Katkısı
Gate: 'K ve M kapandı' sağlanır.
