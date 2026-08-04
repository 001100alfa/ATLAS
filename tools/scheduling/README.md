# ATLAS zamanlanmış görev şablonları (SPEC 048)

`atlas vault backup --auto --keep N` cron/zamanlanmış çalıştırma için
platform-native template'ler. Bu dizindeki dosyalar **şablon** —
kullanıma almadan önce YOL DEĞİŞKENLERİNİ düzenle.

## Dosyalar

| Dosya | Platform | Amaç |
|---|---|---|
| `atlas-vault-backup.service` | Linux (systemd) | Bir kereye mahsus çalıştırma birimi |
| `atlas-vault-backup.timer` | Linux (systemd) | Günlük tetikleyici (03:00 UTC) |
| `atlas-vault-backup.xml` | Windows (Task Scheduler) | Görev tanımı XML |
| `install-linux.sh` | Linux | systemd birim + timer'ı kur |
| `install-windows.ps1` | Windows | `schtasks /Create` ile görev kur |

## Linux (systemd) — hızlı kurulum

```sh
# 1) Değişkenleri düzenle
$EDITOR tools/scheduling/atlas-vault-backup.service
# %I%, %P%, %R% yerine kendi yollarını yaz:
#   %I% → ATLAS git repo tam yolu
#   %P% → atlas komutunun mutlak yolu (which atlas)
#   %R% → archive kökü (varsayılan: <repo>/archive)

# 2) Kur (kullanıcı-modu — root gerektirmez)
bash tools/scheduling/install-linux.sh --keep 30

# 3) Doğrula
systemctl --user list-timers | grep atlas
systemctl --user status atlas-vault-backup.timer

# 4) Manuel tetikle (test)
systemctl --user start atlas-vault-backup.service
```

## Windows (Task Scheduler) — hızlı kurulum

```powershell
# PowerShell'i "Yönetici olarak" aç
# Değişkenleri düzenle: install-windows.ps1 içindeki $RepoRoot / $AtlasBin
powershell -ExecutionPolicy Bypass -File tools\scheduling\install-windows.ps1 -Keep 30

# Doğrula
schtasks /Query /TN "ATLAS Vault Backup"

# Manuel tetikle
schtasks /Run /TN "ATLAS Vault Backup"
```

## Kaldırma

```sh
# Linux
systemctl --user stop atlas-vault-backup.timer
systemctl --user disable atlas-vault-backup.timer
rm ~/.config/systemd/user/atlas-vault-backup.{service,timer}

# Windows
schtasks /Delete /TN "ATLAS Vault Backup" /F
```

## Doğrulama

- Backup dosyaları: `<repo>/archive/vault-YYYY-MM-DD-HHMM.tar.gz`
- Retention: `--keep N` — en yeni N tanesi kalır.
- Audit satırı: `.atlas/audit.jsonl` içinde `atlas-vault / backup-auto`.
- Loglar:
  - Linux: `journalctl --user -u atlas-vault-backup`
  - Windows: Task Scheduler → Görev Geçmişi

## SPEC referansları

- **SPEC 041** — `atlas vault backup` temel komut.
- **SPEC 041.1** — `--auto` explicit intent + `--keep N` retention.
- **SPEC 048** — bu deployment artefaktları (kod değil).
