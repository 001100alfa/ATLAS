# Görev 100 — Teslim

`atlas-doctor.yml` `--diff-history-all` artifact entegrasyonu.

## Uygulama

- Yeni step: `Generate diff-history-all trend (SPEC 091/100)`.
  - `atlas doctor --diff-history-all --json > doctor-diff-history-all.json`.
  - Tarihçe boşsa `||` fallback `{"snapshots":[]}` (SPEC 095 kalıbı).
- Upload artifact listesine `doctor-diff-history-all.json` eklendi.
- Mevcut 2 artifact (`doctor-report.json`, `doctor-diff.txt`)
  DOKUNULMADI (BİT-UYUMLU).

## Kanıt

- +4 test (`tests/test_github_workflows.py` SPEC 100 bölümü):
  - `diff-history-all trend` step + `--diff-history-all --json`.
  - `||` fallback bos snapshots.
  - Upload artifact listesi `doctor-diff-history-all.json` içerir.
  - Mevcut 2 artifact yeri korundu.
- 1351 → **1355 yeşil** (+4), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 070 mevcut `--strict --scan-src` gate + `--auto-baseline` diff
  AYNI.
- SPEC 082 workflow SAYISI değişmedi → README badge tablosu drift YOK.
