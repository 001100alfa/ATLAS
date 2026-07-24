# 04 — Fonksiyonel Olmayanlar  `/nonfunctional`

**Amaç:** Performans, tip, coverage, güvenlik eşiklerini yazmak.

| | |
|---|---|
| **Girdi** | FR seti |
| **Çıktı** | NFR bölümü (ölçülebilir eşikler) |

## Prosedür
1. Varsayılan: mypy strict, coverage>=90, ruff temiz.
2. Göreve özel: süre limiti, bellek, dosya boyutu vb. varsa ekle.
3. Her NFR'nin CI'da NASIL ölçüleceğini belirt.

## Kapıya Katkısı
Kalite kapıları spec'te sözleşmeye bağlanır.
