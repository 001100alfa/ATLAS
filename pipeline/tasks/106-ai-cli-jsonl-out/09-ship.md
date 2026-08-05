# Görev 106 — Teslim

`atlas ai-cli list --outdated --json-lines --out PATH`.

## Uygulama

- `_cmd_ai_cli_list` ön-kontrol: `--out` + not jsonl → exit 2.
- jsonl dalında `out_fh` open("w") + parent.mkdir + IO hatası exit 2.
- `--strict` ile ORTOGONAL (exit_rc korunur, dosyaya yazılır).
- Parser: `--out PATH` metavar.

## Kanıt

- +7 test (`tests/test_cli_ai_cli_jsonl_out.py`):
  - Dosya yazıldı, stdout NDJSON basmaz.
  - Dosya içeriği stdout modu ile AYNI.
  - Parent auto-mkdir.
  - PATH = dizin → exit 2.
  - --out --json-lines yok → exit 2.
  - --out --strict + bulgu → exit 4, dosyaya yazılır.
  - --out YOKSA SPEC 099 stdout AYNI.
- 1374 → **1381 yeşil** (+7), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 099: stdout stream AYNI.
- SPEC 088/094: --json ve --strict davranışları AYNI.
