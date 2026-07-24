# 01 — Referans Doğrulama  `/ref-test`

**Amaç:** Her FR'yi kaynaklı referans değerle test etmek.

| | |
|---|---|
| **Girdi** | SPEC kabul testleri + kod |
| **Çıktı** | Referans test seti (kaynak docstring'de) |

## Prosedür
1. Kaynak (el hesabı/standart/katalog) test docstring'ine yazılır.
2. Analitik: rel_tol=1e-9. Katalog: tolerans + gerekçe.
3. Referansı doğrulanamayan FR -> K sınıfı bulgu olarak işaretle.

## Kapıya Katkısı
Sayısal doğruluk kanıta bağlanır.
