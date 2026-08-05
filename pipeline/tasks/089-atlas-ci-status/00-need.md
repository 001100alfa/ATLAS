# Görev 089 — İhtiyaç

SPEC 082 `ci-status.yml` yalnız push/PR ile tetiklenir. Kimse hafta
boyunca workflow eklemezse README badge tablosu drift'i tespit edilmez;
ayrıca shields.io badge SVG'leri cache'te kalır. Günlük planlı çalışma
gerek.

## Kabul

- Yeni `.github/workflows/atlas-ci-status.yml`.
- `on: schedule: cron` — her gün 06:00 UTC (deterministik).
- `on: workflow_dispatch` — manuel tetik.
- Job: `python tools/scripts/gen_ci_badges.py --check` (drift kontrol).
- Drift bulunursa GitHub issue aç (peter-evans/create-issue-from-file@v5).
- Permissions: `contents: read`, `issues: write`.
- README badge tablosunda yeni workflow satırı görünür (082 gate zaten
  otomatik tutar; script çalıştır + commit).
