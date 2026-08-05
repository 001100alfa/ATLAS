# Görev 105 — Teslim

`atlas archive --list --json-lines --out PATH`.

## Uygulama

- `_cmd_archive_list` jsonl dalında:
  - `--out` + not jsonl → SPEC HATASI exit 2.
  - `out_fh` open("w") + `parent.mkdir` + IO hatası exit 2.
  - Satır bazlı yaz (arşiv + summary).
- Parser: `--out PATH` metavar, default None.

## Kanıt

- +8 test (`tests/test_cli_archive_jsonl_out.py`):
  - Dosya yazıldı, stdout NDJSON basmaz.
  - Dosya içeriği stdout modu ile AYNI.
  - Parent auto-mkdir.
  - PATH = dizin → yazma hatası exit 2.
  - --out --json-lines yok → exit 2.
  - --out --json (tek JSON) → exit 2.
  - --sort-by --limit stream öncesi doğrulama.
  - --out YOKSA SPEC 098 stdout AYNI.
- 1366 → **1374 yeşil** (+8), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 098: `--out` yoksa stdout stream AYNI.
- SPEC 075/079/085/093: pretty/JSON/filter/sort/limit AYNI.
