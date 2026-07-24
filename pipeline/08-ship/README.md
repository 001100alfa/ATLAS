# 08 — SHIP (Teslim)
**Amaç:** Sürümü etiketleyip dağıtmak; işin bittiğini KANITLAMAK.
**Girdi:** Simplify'dan çıkmış main-hazır branch
**Çıktı:** Git tag + CHANGELOG girdisi + release + SHIP-XXX.md

## Prosedür
1. CHANGELOG.md güncelle (SemVer: kırıcı=major, özellik=minor, fix=patch)
2. pyproject version güncelle, `git tag vX.Y.Z`
3. PR merge (squash), `gh release create vX.Y.Z --generate-notes`
4. NEED-XXX'teki başarı ölçütüne dön: SAĞLANDI MI? Kanıtla.

## Çıkış Kapısı
- [ ] CI main'de yeşil
- [ ] Başarı ölçütü kanıtı SHIP raporunda (ölçüm/çıktı)
- [ ] DECISIONS.md güncel; issue kapandı
- [ ] Kullanıcıya tek paragraf teslim özeti verildi
