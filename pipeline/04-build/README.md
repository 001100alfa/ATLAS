# 04 — BUILD
**Amaç:** PLAN'daki paketleri sırayla koda dönüştürmek.
**Girdi:** PLAN-XXX.md | **Çıktı:** src/ altında kod + BUILD-XXX.log.md

## Kurallar
- Branch: feat/issue-N. Paket başına en az 1 commit.
- Spec dışına çıkma dürtüsü = DUR, spec'i güncelle, onay al, devam et.
- Her paket bitişinde hooks otomatik lint+test koşar.

## Çıkış Kapısı
- [ ] Tüm WP'ler kapandı, her biri commit'e bağlandı
- [ ] Spec'ten sapma yok VEYA sapma SPEC'e işlendi
- [ ] BUILD log: her paketin süresi + sorun kaydı
