# Görev 132 — Teslim

`atlas metrics --alert-history-show [PATH] [--limit N] [--json]`.

## Uygulama
- `_cmd_metrics` en başında kısa devre (SPEC 040 kalıbı) —
  metrics özet YAPMAZ, NDJSON log okur.
- Default path `.atlas/alert-history.jsonl` (SPEC 126 uyumlu).
- Bozuk satır atlanır (JSONDecodeError sessiz).
- Pretty tablo: `ts | hit% | threshold% | [channels]`.
- JSON: NDJSON stream + summary `{path,count,total}`.

## Kanıt
- +6 test; +6 → **1553 yeşil**, mypy/ruff/scan temiz.
