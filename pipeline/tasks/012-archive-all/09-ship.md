# 012 — Ship

## Sonuç
`atlas archive --all` toplu arşivleme eklendi. Aday seçimi:
`pipeline/tasks/*/09-ship.md` glob (SHIP aşaması geçmiş görevler).

- **Dry-run varsayılan:** liste + toplam sayı; yıkıcı iş yok.
- **`--apply --yes` ikili onay:** `--yes` olmadan `--apply` → exit 2 +
  stderr uyarı. Çift kapı, tesadüfen toplu silme engellenir.
- **Fail-fast:** ilk hata → dur, kalanları atla, raporla (succeeded /
  failed / skipped listesi). Kısmi başarı görünür.
- **Audit:** her başarılı archive için ayrı `("atlas-archive",
  "archive", <task>)` kaydı; hata da ayrı `("atlas-archive", "error",
  "<task>: <mesaj>")`.

Tekil yol (`atlas archive <task>`, SPEC 007) korundu.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: _cmd_archive --all dallanma,
                                            +_iter_archive_candidates,
                                            +_cmd_archive_all; parser --all/--yes)
tests/test_cli_direct.py                  (+5 test — dry-run liste,
                                            --yes yok exit 2, happy, fail-fast,
                                            boş liste)
pipeline/tasks/012-archive-all/*.md       (5 artefakt)
```

## Sözleşme değişmezliği
- Tekil `atlas archive <task>` sözleşmesi **hiç değişmedi** — mevcut
  6 test 007 yeşil.
- `task` positional artık `nargs="?"` — `--all` verildiğinde yok
  sayılır, verilmezse eskisi gibi zorunlu (yeni SPEC HATASI mesajı).
- Yeni exit kodu YOK — 2 (SPEC) ve 6 (arşiv/handler) yeniden kullanıldı.

## Kullanım örneği
```bash
# Ne arşivlenecek?
atlas archive --all

# Toplu (ikili onay)
atlas archive --all --apply --yes

# Kısmi başarı raporu (fail-fast):
#   arşivlendi: 3/5 görev
#   başarılı: 003-x, 004-y, 005-z
#   başarısız: 006-w — <hata>
#   atlanan: 007-v
```

## Kalite kapıları
- pytest: **407 passed** (402 → +5)
- coverage: **%93.69**
- mypy strict + ruff: temiz
- `atlas scan src`: sır yok

## Branch
`feat/012-archive-all` — 011 üstünde tek commit.

## Bekleyen
- `--older-than N gün` filtresi — kapsam DIŞI (YAGNI)
- Paralel arşivleme — kapsam DIŞI
- İnteraktif y/N prompt — kapsam DIŞI (script'lenebilir yeter)
