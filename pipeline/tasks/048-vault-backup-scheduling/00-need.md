# Görev 048 — İhtiyaç

SPEC 041.1 `atlas vault backup --auto --keep N` cron için tasarlandı
(explicit intent + retention). Ama kullanıcı hâlâ platform-native
zamanlayıcı için template yazmak zorunda:
- Linux: `.service` + `.timer` yaz + `systemctl --user enable`
- Windows: XML üret + `schtasks /Create /XML`

Bu operasyonel adım "birinci sınıf deployment" gerektiriyor.

## Kabul kriteri

Bu görev kod değil, deployment artefaktı. `tools/scheduling/` altında:

- `README.md` — Linux + Windows kurulum adımları
- **Linux (systemd --user)**:
  - `atlas-vault-backup.service` — oneshot birim, `%I%/%P%/%R%/%K%`
    placeholder'ları
  - `atlas-vault-backup.timer` — günlük 03:00 UTC + `Persistent=true`
    (kaçırılan çalıştırma açılışta) + `RandomizedDelaySec` jitter
  - `install-linux.sh` — POSIX shell, sed ile placeholder doldur,
    `systemctl --user daemon-reload + enable --now`
- **Windows (Task Scheduler)**:
  - `atlas-vault-backup.xml` — v1.2 Task XML; `__ATLAS_BIN__` /
    `__ARCHIVE_ROOT__` / `__REPO_ROOT__` / `__KEEP__` placeholder'ları
  - `install-windows.ps1` — `[CmdletBinding()]`, XML replace,
    `schtasks /Delete /F` (idempotent) + `schtasks /Create /XML`

## Kabul testleri

- Şablon dosyalarının hepsi mevcut
- systemd .service: 4 placeholder + `vault backup --auto` argv
- systemd .timer: `OnCalendar=*-*-* 03:00:00` + `Persistent=true` +
  `RandomizedDelaySec`
- install-linux.sh: shebang + `set -eu` + sed komutları
- Task XML valid parse (xml.etree) + 4 placeholder + `CalendarTrigger`
  günlük 03:00 + `RandomDelay PT10M`
- install-windows.ps1: `[CmdletBinding()]` + Replace çağrıları +
  `schtasks /Delete + /Create`

## Riskli

- Windows XML UTF-16 encoding zorunlu (Task Scheduler talebi);
  install-windows.ps1 `[System.IO.File]::WriteAllText(..., Unicode)`
  ile temp XML üretir. Şablon dosyası UTF-8 (test parse etsin diye);
  install-windows.ps1 çıkışında UTF-16'ya çevrilir.
- Yol placeholder'ları sed/Replace ile doldurulur — special char
  içermeyen makul yollar bekleniyor. Boşluklu yollar için Windows
  tarafında argümanlar zaten çift-tırnaklı.
- systemd --user birimleri kullanıcı oturumu kapalıyken çalışmaz —
  server ortamında `loginctl enable-linger $USER` gerek olabilir
  (README notu koymalıyım).
