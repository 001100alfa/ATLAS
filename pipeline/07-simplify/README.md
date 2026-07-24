# 07 — SIMPLIFY (Sadeleştirme)
**Amaç:** Çalışan kodu KÜÇÜLTMEK. Her satır bakım yüküdür.
Davranış değişmez — testler garanti eder (önce yeşil, sonra yeşil).
**Girdi:** Review'dan çıkmış kod | **Çıktı:** SIMPLIFY-XXX.md + refactor commit'leri

## Kontrol Listesi
- Ölü kod / kullanılmayan import / erişilmeyen dal
- Tekrar eden mantık -> tek fonksiyon
- Public API: dışarıdan çağrılmayan şey private olsun
- "Belki lazım olur" kodu -> SİL (git hatırlar)
- Doküman <-> kod tutarlılığı (docstring güncel mi)

## Çıkış Kapısı
- [ ] Satır sayısı azaldı veya azalmama gerekçesi yazıldı
- [ ] Testler DEĞİŞMEDEN yeşil (davranış korundu kanıtı)
- [ ] Public API yüzeyi listelendi, her öğesi gerekçeli
