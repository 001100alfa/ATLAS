# 05 — TEST
**Amaç:** SPEC'teki her FR'nin kanıtla doğrulanması.
**Girdi:** BUILD çıktısı + SPEC kabul testleri
**Çıktı:** tests/ altında kod + TEST-XXX.md rapor

## Test Politikası
1. Referans testler: el hesabı/katalog/standart değeriyle (kaynak yazılır)
2. Kenar durumlar: sıfır, negatif, sınır, taşma
3. Hata sözleşmesi: doğru exception, doğru mesaj
4. Fizik kontrolü: Wpl>Wel gibi alan-bilgisi invariant'ları

## Çıkış Kapısı
- [ ] FR <-> test eşleme tablosu tam (izlenebilirlik)
- [ ] Coverage >= %90, mypy strict temiz
- [ ] tester subagent bağımsız koştu, raporu eklendi
