# Görev 119 — İhtiyaç

SPEC 089 `atlas-ci-status.yml` günlük drift scan yapar. Haftalık toplu
tarama + geçmiş görsel tetik için ayrı cron gerek (Pazartesi sabahı
sprint retrospektif için özet).

## Kabul

- `.github/workflows/atlas-ci-status.yml` ikinci cron:
  `0 7 * * 1` (her Pazartesi 07:00 UTC = Istanbul 10:00).
- Aynı job (`drift-scan`) — mevcut daily davranışı BOZULMADAN yeni
  tetikleyici eklenir (schedule listesine ek satır).
- workflow_dispatch korunur.
- İki cron aynı işi yapar (drift → issue); haftalık tetik retrospektif
  hatırlatıcı görev yapar.
