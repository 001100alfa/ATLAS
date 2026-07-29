# 017 — Ship

## Sonuç
`atlas archive --all --auto` yaş filtresi eklendi. Aday seçimi:
`pipeline/tasks/*/09-ship.md` mtime'ı `ATLAS_ARCHIVE_AGE_DAYS`
(varsayılan 7) günden eski olanlar. Taze görevler atlanır.

- **Cron/hook uyumu:** kullanıcı Windows Görev Zamanlayıcı veya
  `cron` ile `atlas archive --all --auto --apply --yes` çalıştırıp
  eski görevlerin otomatik arşive taşınmasını sağlayabilir.
- **012 uyum:** `--auto` olmadan `--all` mevcut davranış (yaş yok,
  hepsi aday) — 012 mevcut 5 test yeşil kaldı.
- **Çift kapı korunur:** `--auto --apply --yes` üçlü hâlâ zorunlu.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: _iter_archive_candidates
                                            age_days paramı, +_read_archive_age_env,
                                            _cmd_archive_all --auto dallanma,
                                            parser --auto flag)
tests/test_cli_direct.py                  (+4 test — --auto taze atla, eski
                                            seç, env override, --auto yok=012)
pipeline/tasks/017-archive-auto/*.md      (5 artefakt)
```

## Sözleşme değişmezliği
- 012 mevcut `--all` yolu ve testleri **hiç değişmedi**.
- 007 tekil `atlas archive <task>` yolu **hiç değişmedi**.
- `_iter_archive_candidates` yeni parametre **default=None** →
  012 davranışı korundu.
- Yeni exit kodu YOK — 2 (SPEC/--yes yok) ve 6 (arşiv hatası) korundu.

## Kalite kapıları
- pytest: **444 passed** (440 → +4)
- mypy strict + ruff: temiz

## Branch
`feat/017-archive-auto` — 016 üstünde tek commit.

## Kullanım örneği
```bash
# Ne arşivlenecek (7 günden eski)?
atlas archive --all --auto

# Cron/hook (haftalık): 30 günden eski görevleri sessiz arşivle
ATLAS_ARCHIVE_AGE_DAYS=30 atlas archive --all --auto --apply --yes
```

Windows Görev Zamanlayıcı:
```
Program:  C:\Users\...\uv.exe
Args:     run atlas archive --all --auto --apply --yes
Trigger:  Weekly, Sunday 03:00
```

Cron (Linux/macOS):
```
0 3 * * 0 cd /path/to/atlas && uv run atlas archive --all --auto --apply --yes
```

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_ARCHIVE_AGE_DAYS` | `--auto` eşiği gün (varsayılan 7) |

## Bekleyen
- `atlas run` sonu otomatik ship+archive tetikleyicisi — Görev 017.1
  (op zamanlayıcı yerine ATLAS-içi hook).
