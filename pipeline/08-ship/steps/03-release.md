# 03 — Yayın Prosedürü  `/release`

**Amaç:** PR merge + tag + GitHub release zinciri.

| | |
|---|---|
| **Girdi** | CI yeşil branch |
| **Çıktı** | Merge + vX.Y.Z tag + release notları |

## Prosedür
1. PR aç (squash), CI TÜM kapılardan geçmeli.
2. Merge sonrası: git tag vX.Y.Z, gh release create --generate-notes.
3. Release'e SHIP raporu linki eklenir.

## Kapıya Katkısı
Gate: 'CI main'de yeşil' sağlanır.
