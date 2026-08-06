# Görev 118 — Teslim

`atlas ai-cli status <name> --json-lines [--out PATH]`.

## Uygulama
- `_cmd_ai_cli_status`: `jsonl_mode` + `--out` ön-kontrol.
  - `--json + --json-lines` → MUTEX exit 2.
  - `--out + not jsonl` → exit 2.
- NDJSON: 8 alan satırı `{"field","value"}` + son satır
  `{"type":"summary","name","up_to_date"}`.
- `--out` ile parent auto-mkdir + IO hatası exit 2.
- Parser: `--json-lines` + `--out` metavar.

## Kanıt
- +6 test; 1468 → **1474 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 037.4 `--json` çıktı içerik AYNI.
