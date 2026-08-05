# Görev 100 — İhtiyaç

SPEC 070 `atlas-doctor.yml` `--auto-baseline` tek snapshot ile
karşılaştırır. SPEC 091 tüm tarihçe ile toplu diff mevcut; workflow
`--diff-history-all` artifact'ı da üretmeli (trend takibi).

## Kabul

- `.github/workflows/atlas-doctor.yml` yeni step: `Generate
  diff-history-all trend`.
- `atlas doctor --diff-history-all --json > doctor-diff-history-all.json`
  → artifact.
- `.atlas/doctor-history/` tarihçe boşsa/yoksa `||` fallback boş JSON
  `{"snapshots":[]}` (workflow durmaz — SPEC 095 fail-safe kalıbı).
- Upload artifact listesine `doctor-diff-history-all.json` eklendi.
- Mevcut 2 artifact (`doctor-report.json`, `doctor-diff.txt`)
  DOKUNULMADI (BİT-UYUMLU).
- README badge tablosu etkilenmez (workflow SAYISI aynı).
