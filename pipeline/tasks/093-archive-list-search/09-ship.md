# Görev 093 — Teslim

`atlas archive --list --name-match PATTERN [--sort-by KEY] [--desc]
[--limit N] [--json]`.

## Uygulama

- `_cmd_archive_list` içinde SPEC 093 bloğu:
  - `re.compile(name_match)` (geçersiz regex → SPEC HATASI exit 2).
  - `entries = [e for e in entries if pat.search(e["archive"])]`.
  - Filtre sort ÖNCE (sort filter'lı liste üzerinde çalışır).
- Boş sonuç pretty ayrımı: `--name-match` verildiyse `(esleme yok)`,
  aksi hâlde SPEC 075 `(arsiv yok)` BİT-UYUMLU.
- Parser: `--name-match PATTERN` metavar, default None.

## Kanıt

- +8 test (`tests/test_cli_archive_list_name_match.py`):
  - Prefix regex (`^backup`) filtre.
  - Geçersiz regex → exit 2 net mesaj.
  - Boş sonuç → `(esleme yok)` + "0 arsiv".
  - Boş dizin + name-match yok → SPEC 075 `(arsiv yok)` BİT-UYUMLU.
  - name-match sort ÖNCE (task-bbb > task-aaa; backup filtreli).
  - name-match + sort size desc + limit 2 tam zincir.
  - Regex substring (`\d{4}-\d{2}`).
  - --name-match YOKSA SPEC 075 default name alfabetik AYNI.
- 1290 → **1298 yeşil** (+8), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 075: default name alfabetik + tam liste + (arsiv yok) mesajı
  BİT-UYUMLU (name-match yoksa).
- SPEC 079/085 sort/limit zinciri AYNI.
- SPEC 065 `--search` (içerik arama) DOKUNULMADI (ORTOGONAL).
