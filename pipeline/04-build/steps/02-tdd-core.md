# 02 — TDD Çekirdeği  `/tdd-core`

**Amaç:** Önce kabul testini yaz (kırmızı), sonra kodu (yeşil).

| | |
|---|---|
| **Girdi** | SPEC kabul testleri |
| **Çıktı** | Test-önce implementasyon döngüsü |

## Prosedür
1. SPEC'teki referans değerli testi AYNEN koda dök -> kırmızı.
2. Minimum kodu yaz -> yeşil. Refactor -> hâlâ yeşil.
3. Referanssız kod yazma dürtüsü = spec'e dön sinyali.

## Kapıya Katkısı
Kod, spec'ten sapamaz — test tasması takılı.
