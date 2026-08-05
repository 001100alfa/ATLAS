# Görev 065 — Teslim

`atlas archive --search PATTERN [--json]`.

## Uygulama

- `_search_archive_contents(archive_root, pattern)`: `re.compile` +
  `tarfile.open('r:gz').getnames()` — tar açılmaz. Bozuk tar skipped.
- `_cmd_archive_search`: 2-yollu hata (arc kökü yok / regex geçersiz)
  → exit 2. `--json` bit-hassas, insan çıktısı sayaç + arşiv listesi.
- `_cmd_archive` dispatcher: `--search` en önde (yıkıcı işlemlerden önce).
- Parser: `--search PATTERN` + `--json` bayrakları.

## Kanıt

- +13 test (`tests/test_cli_archive_search.py`):
  - Birim (7): dir yok, bulgu yok, tek eşleşme, çoklu sıra, regex hata,
    bozuk tar skip, (?i) case-insensitive.
  - CLI (6): arc yok exit 2, regex geçersiz exit 2, insan çıktısı, bulgu
    yok mesajı, --json, diğer archive modları bit-uyumlu.
- 1035 → **1048 yeşil**, 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 007/012/017/033 archive komutları BİT-UYUMLU.
- `--search` en önde branch — yıkıcı işlemlere dokunmaz (read-only).
