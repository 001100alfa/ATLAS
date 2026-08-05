# Görev 075 — Teslim

`atlas archive --list [--json]` — arşiv metadata listesi.

## Uygulama

- `_list_archive_entries(archive_root)`: her `*.tar.gz` için 7-alanlı
  dict. `<task_id>-YYYY-MM-DD.tar.gz` → task_id + date; atipik → stem
  fallback. Bozuk tar → member_count=-1. Alfabetik sıra.
- `_cmd_archive_list`: `--json` bit-hassas; insan çıktısı hizalı tablo.
- Dispatcher: `--list` en önde (SPEC 007/012/033/065/071'den önce).
- Parser: `--list` bayrağı; mevcut `--json` bayrağı SPEC 075 için de.

## Kanıt

- +11 test:
  - Birim (6): arşiv yok, boş dizin, task_id+date ayırma, atipik
    fallback, alfabetik sıra, bozuk tar member_count=-1.
  - CLI (5): arc yok exit 2, insan çıktısı, boş mesaj, --json çıktı,
    diğer archive modları bit-uyumlu.
- 1133 → **1144 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 007/012/017/033/065/071 archive komutları BİT-UYUMLU.
- `--list` read-only, yıkıcı yollara dokunmaz.
