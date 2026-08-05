# Görev 071 — Teslim

`atlas archive --restore --search PATTERN` — SPEC 065 + SPEC 033 birleşim.

## Uygulama

- `cli.py::_cmd_archive_restore`:
  - `--search PATTERN` verildiyse `_search_archive_contents` (SPEC 065)
    ile arşiv arama; 0 → exit 6, 2+ → exit 2 (belirsizlik listesi
    stderr), tek → arşiv adından task_id çıkar.
  - `<task_id>-YYYY-MM-DD.tar.gz` format: son 11 char (`-YYYY-MM-DD`)
    kaldırılır; farklı format → stem fallback.
- `--restore` parser `nargs="?"` `const=""` — bayraksız çağrıya izin
  ver (search-based mod için).
- `_cmd_archive` dispatcher: `--restore is not None` → restore branch;
  aksi `--search` → list-only.

## Kanıt

- +7 test (`tests/test_cli_archive_restore_search.py`):
  - --restore --search tek eşleşme dry-run + apply (gerçek restore).
  - Bulgu yok → exit 6.
  - Çoklu eşleşme → exit 2 + stderr listesi.
  - Regex geçersiz → exit 2.
  - --restore <id> (search yok) SPEC 033 bit-uyumlu.
  - --search PATTERN (restore yok) SPEC 065 bit-uyumlu.
- Mevcut 25 SPEC 033 + 065 testi BİT-UYUMLU.
- 1092 → **1099 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 007/012/017/033/065 hepsi BİT-UYUMLU.
- Exit kodları: 0/2/3/6 sınıfı (yeni kod yok).
