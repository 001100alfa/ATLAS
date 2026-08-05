# Görev 107 — İhtiyaç

SPEC 041 vault backup + SPEC 101 split + SPEC 102 restore mevcut ama
CI/scheduled yedek YOK. Kullanıcı manuel çalıştırıyor. Vault-health
(SPEC 056) sadece read-only. Backup workflow gerek: günlük scheduled
+ artifact.

## Kabul

- Yeni `.github/workflows/atlas-vault.yml`.
- `on.schedule: cron: "0 3 * * *"` — her gün 03:00 UTC (Istanbul 06:00,
  gece iş yükü düşük saat).
- `on.workflow_dispatch: {}` — manuel tetik.
- Permissions: `contents: read`.
- Job `backup`: `atlas vault backup --auto --split 50 --keep 7`.
  - `--split 50 MB` parçalı (GitHub artifact 2 GB sınırı için).
  - `--keep 7` retention (7 gün eski yedek).
- Upload artifact `vault-backup-parts` (30 gün retention).
- README badge tablosu regen (yeni workflow).
- Vault yoksa (`test -d vault`) skip → workflow durmaz.
