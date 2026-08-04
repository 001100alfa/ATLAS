# Görev 048 — Teslim

`tools/scheduling/` — Linux systemd + Windows Task Scheduler şablonları.

## Uygulama

- **`tools/scheduling/README.md`** — kurulum + doğrulama + kaldırma.
- **Linux (systemd --user)**:
  - `atlas-vault-backup.service` — `Type=oneshot`, `Nice=15`,
    `IOSchedulingClass=idle`, `Restart=on-failure` (3x, 5dk arayla).
  - `atlas-vault-backup.timer` — günlük 03:00 UTC, `Persistent=true`,
    `RandomizedDelaySec=600` (jitter).
  - `install-linux.sh` — `--keep N` argümanı; sed ile 4 placeholder
    (`%I%/%P%/%R%/%K%`) doldurur; `systemctl --user enable --now`.
- **Windows (Task Scheduler)**:
  - `atlas-vault-backup.xml` — Task v1.2 XML; günlük 03:00 UTC + 10dk
    jitter; `MultipleInstancesPolicy=IgnoreNew`; `ExecutionTimeLimit=PT1H`.
  - `install-windows.ps1` — `[CmdletBinding()]` ile parametrik
    (Keep/RepoRoot/AtlasBin); XML placeholder Replace; UTF-16 temp
    XML üretimi; `schtasks /Delete /F` (idempotent) + `/Create /XML`.

## Kanıtlar

- +13 test (`tests/test_scheduling_templates.py`):
  - Şablon dosyalarının hepsi mevcut (parametrize x6)
  - systemd .service: placeholder'lar + argv + `Type=oneshot`
  - systemd .timer: OnCalendar + Persistent + RandomizedDelaySec
  - install-linux.sh: shebang + set -eu + sed komutları + systemctl
  - Task XML: valid parse + 4 placeholder + Exec elementi
  - Task XML: günlük 03:00 + DaysInterval=1 + RandomDelay PT10M
  - install-windows.ps1: CmdletBinding + Replace + schtasks
  - README: platform başlıkları + SPEC referansları
- 857 → **870 yeşil**, 12 skip, cov aynı %91.10 (kod eklenmedi).
- `uv run mypy src` temiz.
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Deployment artefaktları (kod değil):
  - Linux: `bash tools/scheduling/install-linux.sh --keep 30`
  - Windows: `powershell -File tools/scheduling/install-windows.ps1 -Keep 30`

## Değişmeyen sözleşme

- `atlas vault backup --auto --keep N` (SPEC 041.1) BİT-UYUMLU.
- Kod tarafında hiçbir değişiklik YOK — yalnız tools/ altında yeni
  dosyalar.
