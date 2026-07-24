# 05 — Davranış Kanıtı  `/prove-behavior`

**Amaç:** Sadeleştirmenin hiçbir davranışı değiştirmediğini kanıtlamak.

| | |
|---|---|
| **Girdi** | Tüm refactor commit'leri |
| **Çıktı** | SIMPLIFY-XXX.md (önce/sonra + yeşil kanıt) |

## Prosedür
1. Testlere DOKUNULMADI mı? git diff tests/ boş olmalı.
2. Tam set yeşil + coverage düşmedi kanıtını yapıştır.
3. Önce/sonra satır sayısı; artmışsa gerekçe zorunlu.

## Kapıya Katkısı
Gate: 'testler değişmeden yeşil' sağlanır.
