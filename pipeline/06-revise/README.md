# 06 — REVISE (Gözden Geçirme)
**Amaç:** Bağımsız gözle hata bulmak. Yazan gözden geçirmez —
reviewer subagent + (kritik işte) kullanıcı.
**Girdi:** TEST raporu + diff | **Çıktı:** REVIEW-XXX.md + düzeltme commit'leri

## Bulgu Sınıfları
- K (kritik): yanlış sonuç, güvenlik -> merge engeli
- M (majör): kenar durum, birim riski -> bu turda düzelt
- m (minör): stil, isimlendirme -> düzelt veya gerekçeyle reddet

## Çıkış Kapısı
- [ ] Tüm K ve M bulgular kapandı (commit referanslı)
- [ ] Reddedilen minörler gerekçeli
- [ ] Kalıcı ders -> DECISIONS.md'ye [HATA] etiketiyle
