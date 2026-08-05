# Görev 070 — İhtiyaç

SPEC 056 vault-health GHA workflow'u PR'da vault graf sağlığını gate ediyor.
Ama `atlas doctor` (DECISIONS drift + entry count + vault + scan_src +
optional http_check) CI'de yok. Kod PR'ları vault-only workflow'u
tetiklemez → doctor bulguları geç fark edilir.

## Kabul

- `.github/workflows/atlas-doctor.yml`.
- Tetikleyici: push[main] + PR, `src/` + `DECISIONS.md` + workflow YAML +
  `.atlas/doctor-baseline.json` path filtresi.
- Job doctor: ubuntu-latest, timeout 5dk.
- Adımlar:
  1. checkout + setup-uv + uv sync.
  2. `atlas doctor --strict --scan-src --json > doctor-report.json`
     (fresh strict, rc → GITHUB_OUTPUT).
  3. Baseline varsa `atlas doctor --strict --auto-baseline > doctor-diff.txt`
     (SPEC 062 delta, rc → GITHUB_OUTPUT); yoksa "baseline yok" mesajı.
  4. artifact upload (30 gün retention).
  5. PR comment fail'de.
  6. Fail step: `rc_strict != '0' OR rc_diff != '0'` → exit 1.
- Env: `ATLAS_STRICT_DRIFT_DAYS: 30`, `ATLAS_MIN_DECISIONS_ENTRIES: 1`
  (CI'da gevşek eşikler; kullanıcı repo policy'sine göre override eder).
