# 03 — PLAN
**Amaç:** SPEC'i sıralı, riskli noktaları işaretli iş paketlerine bölmek.
**Girdi:** Onaylı SPEC-XXX.md
**Çıktı:** `PLAN-XXX.md` + büyük mimari karar varsa `docs/adr/ADR-N.md`

## Çıkış Kapısı
- [ ] Her iş paketi <= yarım gün; çıktısı ve doğrulaması tanımlı
- [ ] Bağımlılık sırası çizildi
- [ ] En riskli paket İLK sıraya alındı (fail-fast)
- [ ] Geri dönüş planı: paket başarısızsa ne olacak
